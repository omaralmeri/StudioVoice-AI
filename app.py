import os
import gc
import uuid
import subprocess
import torch
import torchaudio
import soundfile as sf
import numpy as np
import gradio as gr
from resemble_enhance.enhancer.inference import enhance

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"✅ Device Initialized: {device.upper()}")

# ==================== 1. محرك استوديو التنقية والماسترينج ====================
def enhance_audio_engine(audio_tensor, sr, lambd_val):
    chunk_sec = 20
    overlap_sec = 2
    chunk_size = int(chunk_sec * sr)
    overlap_size = int(overlap_sec * sr)
    step = chunk_size - overlap_size
    total_samples = audio_tensor.shape[0]
    
    if total_samples <= chunk_size:
        with torch.no_grad():
            enhanced, out_sr = enhance(
                audio_tensor, sr, device=device, 
                nfe=64, solver="midpoint", lambd=lambd_val, tau=0.5
            )
        return enhanced.cpu().numpy(), out_sr
    
    output_chunks = []
    num_chunks = int(np.ceil((total_samples - overlap_size) / step))
    out_sr = None
    
    for i in range(num_chunks):
        start = i * step
        end = min(start + chunk_size, total_samples)
        chunk = audio_tensor[start:end]
        
        with torch.no_grad():
            chunk_enhanced, out_sr = enhance(
                chunk, sr, device=device, 
                nfe=64, solver="midpoint", lambd=lambd_val, tau=0.5
            )
        output_chunks.append(chunk_enhanced.cpu().numpy())
        del chunk, chunk_enhanced
        if device == "cuda":
            torch.cuda.empty_cache()
    
    out_overlap = int(overlap_sec * out_sr)
    out_step = int(step * (out_sr / sr))
    total_len = out_step * (len(output_chunks) - 1) + len(output_chunks[-1])
    merged = np.zeros(total_len, dtype=np.float32)
    
    for i, c in enumerate(output_chunks):
        c_start = i * out_step
        c_end = c_start + len(c)
        if i == 0:
            merged[c_start:c_end] += c
        else:
            fade_in = np.linspace(0, 1, out_overlap)
            c[:out_overlap] *= fade_in
            merged[c_start : c_start + out_overlap] *= (1 - fade_in)
            merged[c_start:c_end] += c
            
    return merged, out_sr

def process_studio(file_up, mic_rec, mix_val, denoise_active, master_active):
    input_file = mic_rec if mic_rec is not None else file_up
    if not input_file:
        raise gr.Error("الرجاء رفع ملف أو تسجيل صوت أولاً!")
        
    input_path = input_file if isinstance(input_file, str) else getattr(input_file, "name", str(input_file))
    session_id = uuid.uuid4().hex[:8]
    raw_wav = f"raw_{session_id}.wav"
    temp_wav = f"temp_{session_id}.wav"
    final_wav = f"Studio_Master_{session_id}.wav"
    final_video = f"Video_{session_id}.mp4"
    
    try:
        cmd_extract = [
            "ffmpeg", "-y", "-i", input_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1",
            raw_wav
        ]
        subprocess.run(cmd_extract, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        dwav, sr = torchaudio.load(raw_wav)
        dwav = dwav.mean(dim=0)
        
        lambd_val = 0.9 if denoise_active else 0.1
        enhanced_audio, out_sr = enhance_audio_engine(dwav, sr, lambd_val)
        
        if mix_val < 100:
            raw_np = dwav.cpu().numpy()
            min_l = min(len(raw_np), len(enhanced_audio))
            w = mix_val / 100.0
            enhanced_audio = (enhanced_audio[:min_l] * w) + (raw_np[:min_l] * (1.0 - w))
            
        sf.write(temp_wav, enhanced_audio, out_sr)
        
        if master_active:
            cmd_master = [
                "ffmpeg", "-y", "-i", temp_wav,
                "-af", "highpass=f=30,loudnorm=I=-14:LRA=7:TP=-1.5",
                "-ar", "48000",
                final_wav
            ]
            subprocess.run(cmd_master, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            final_wav = temp_wav
            
        is_video = input_path.lower().endswith(('.mp4', '.mov', '.mkv', '.avi', '.webm'))
        out_video = None
        if is_video:
            cmd_video = [
                "ffmpeg", "-y", "-i", input_path, "-i", final_wav,
                "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
                "-map", "0:v:0", "-map", "1:a:0",
                "-shortest", final_video
            ]
            subprocess.run(cmd_video, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            out_video = final_video
            
        return raw_wav, final_wav, out_video
    finally:
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()

# ==================== 2. محرك استخراج الصوت السريع ====================
def fast_extract_audio(video_file, audio_format):
    if not video_file:
        raise gr.Error("الرجاء رفع مقطع فيديو أولاً!")
        
    input_path = video_file if isinstance(video_file, str) else getattr(video_file, "name", str(video_file))
    session_id = uuid.uuid4().hex[:8]
    
    if "MP3" in audio_format:
        output_file = f"Extracted_Audio_{session_id}.mp3"
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vn", "-acodec", "libmp3lame", "-b:a", "320k",
            output_file
        ]
    else:
        output_file = f"Extracted_Audio_{session_id}.wav"
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "48000",
            output_file
        ]
        
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0 or not os.path.exists(output_file):
        raise gr.Error("تعذر استخراج الصوت، تأكد من سلامة ملف الفيديو!")
        
    return output_file

# ==================== واجهة المستخدم Gradio ====================
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue")) as app:
    gr.Markdown("# 🎛️ منصة هندسة ومعالجة الصوتيات الذكية (StudioVoice AI)")
    
    with gr.Tabs():
        with gr.TabItem("🎙️ استوديو التنقية والماسترينج (Studio Voice)"):
            with gr.Row():
                with gr.Column():
                    with gr.Tabs():
                        with gr.TabItem("📁 رفع فيديو أو صوت"):
                            f_in = gr.File(label="اسحب ملف فيديو أو صوت", file_types=["audio", "video"])
                        with gr.TabItem("🎙️ تسجيل صوتي مباشر"):
                            m_in = gr.Audio(sources=["microphone"], type="filepath", label="سجل بصوتك مباشرة")
                    
                    with gr.Accordion("🎛️ خيارات جودة الصوت", open=True):
                        mix_s = gr.Slider(50, 100, value=90, step=5, label="نسبة خامة الاستوديو (Mix %)")
                        denoise_c = gr.Checkbox(label="عزل الضجيج والمكيف", value=True)
                        master_c = gr.Checkbox(label="ماسترينج العلو (-14 LUFS)", value=True)
                        
                    btn_studio = gr.Button("بدء التنقية بالذكاء الاصطناعي ⚡", variant="primary", size="lg")
                    
                with gr.Column():
                    a_orig = gr.Audio(label="الصوت الأصلي الخام", type="filepath")
                    a_studio = gr.Audio(label="✨ صوت الاستوديو النقي (Mastered WAV)", type="filepath")
                    v_out = gr.Video(label="🎬 الفيديو المدمج بالصوت الجديد")
                    
            btn_studio.click(
                fn=process_studio,
                inputs=[f_in, m_in, mix_s, denoise_c, master_c],
                outputs=[a_orig, a_studio, v_out]
            )

        with gr.TabItem("⚡ استخراج الصوت السريع من الفيديو (Instant Extract)"):
            gr.Markdown("### استخراج المسار الصوتي الأصلي من أي فيديو في ثوانٍ معدودة.")
            with gr.Row():
                with gr.Column():
                    vid_fast_in = gr.File(label="ارفع مقطع الفيديو هنا", file_types=["video"])
                    format_choice = gr.Radio(
                        choices=["WAV (أعلى جودة نقية غير مضغوطة)", "MP3 (جودة 320kbps وحجم خفيف)"],
                        value="WAV (أعلى جودة نقية غير مضغوطة)",
                        label="صيغة الصوت المستخرج"
                    )
                    btn_fast = gr.Button("استخراج الصوت فوراً 🚀", variant="secondary", size="lg")
                    
                with gr.Column():
                    fast_audio_out = gr.Audio(label="🎧 ملف الصوت المستخرج (جاهز للتحميل)", type="filepath")
                    
            btn_fast.click(
                fn=fast_extract_audio,
                inputs=[vid_fast_in, format_choice],
                outputs=[fast_audio_out]
            )

if __name__ == "__main__":
    app.launch(share=True)
