import const_voices as cstv
import sounddevice as sd
import soundfile as sf
import simpleaudio as sa
import scipy.io.wavfile as wav
import numpy as np
import subprocess as sb 

import traceback
import os
import math
import warnings
import threading
import random
import time 
import webbrowser
import urllib.parse
import string

from faster_whisper import WhisperModel
from simpletts import tts
from ollama import chat

ENABLE_DEBUG = 0 

def debug(db):
    if ENABLE_DEBUG:
        print(db)

def Bar(text, total_length=60):
    text = f" {text} "
    text_len = len(text)
    if text_len >= total_length:
        return text[:total_length]
    
    remaining = total_length - text_len
    left_eq = remaining // 2
    right_eq = remaining - left_eq
    
    bar = '=' * left_eq + text + '=' * right_eq
    return bar

def Banner():
    banner = '''
 /$$$$$$$$                         /$$$$$$                     /$$             /$$                           /$$    
| $$_____/                        /$$__  $$                   |__/            | $$                          | $$    
| $$    /$$    /$$ /$$$$$$       | $$  \ $$  /$$$$$$$ /$$$$$$$ /$$  /$$$$$$$ /$$$$$$    /$$$$$$  /$$$$$$$  /$$$$$$  
| $$$$$|  $$  /$$/|____  $$      | $$$$$$$$ /$$_____//$$_____/| $$ /$$_____/|_  $$_/   |____  $$| $$__  $$|_  $$_/  
| $$__/ \  $$/$$/  /$$$$$$$      | $$__  $$|  $$$$$$|  $$$$$$ | $$|  $$$$$$   | $$      /$$$$$$$| $$  \ $$  | $$    
| $$     \  $$$/  /$$__  $$      | $$  | $$ \____  $$\____  $$| $$ \____  $$  | $$ /$$ /$$__  $$| $$  | $$  | $$ /$$
| $$$$$$$$\  $/  |  $$$$$$$      | $$  | $$ /$$$$$$$//$$$$$$$/| $$ /$$$$$$$/  |  $$$$/|  $$$$$$$| $$  | $$  |  $$$$/
|________/ \_/    \_______/      |__/  |__/|_______/|_______/ |__/|_______/    \___/   \_______/|__/  |__/   \___/  
                                                                                                                    
                                                                                                                    
    '''
    print(banner)

def DisableErrorMsgs():
    debug('disable_error_flags_in_terminal')
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)
    os.environ["PYTORCH_JIT_LOG_LEVEL"] = "ERROR"
    os.environ["TRANSFORMERS_VERBOSITY"] = "error"

def Spinner_thread(stop_event, msg):
    spinner_chars = ['|', '/', '-', '\\']
    idx = 0
    start_time = time.time()
    while not stop_event.is_set():
        elapsed = int(time.time() - start_time)
        print(f"\r{msg} {spinner_chars[idx % len(spinner_chars)]} Elapsed: {elapsed}s", end='', flush=True)
        idx += 1
        time.sleep(0.1)
    # print("\r" + " " * 20 + "\r", end='', flush=True)  # Clear the line after stopping
def RecordThread(sample_rate, stop_event_record):
    global frames
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
        while not stop_event_record.is_set():
            data, _ = stream.read(1024)
            frames.append(data)

def Record(outputfile, volume_boost=1):
    global  frames
    sample_rate = 44100
    frames = []
    print(Bar("RECORDING"))

    stop_event_record = threading.Event()
    stop_event_spin = threading.Event()
    thread_record = threading.Thread(target=RecordThread, args=(sample_rate,stop_event_record))
    thread_spin = threading.Thread(target=Spinner_thread, args=(stop_event_spin,"[Click Enter to end recording] Recording... "))
    thread_record.start()
    thread_spin.start()

    input()

    stop_event_spin.set()
    thread_spin.join()
    stop_event_record.set()
    thread_record.join()

    audio = np.concatenate(frames)
    audio = audio.astype(np.float32) * volume_boost
    audio = np.clip(audio, -32768, 32767).astype(np.int16)
    wav.write(outputfile, sample_rate, audio)
    print(f'{Bar(f"Recording saved as {outputfile}")}\n')

def Transcribter(outputfile, delete=1):
    print(Bar("TRANSCRIBTER"))
    stop_event_spin = threading.Event()
    thread_spin = threading.Thread(target=Spinner_thread, args=(stop_event_spin, "Transcribing... ",))
    thread_spin.start()
    # get total logical threads (e.g., 8 on a 4-core/8-thread CPU)
    total_threads = os.cpu_count() or 2  # fallback in case detection fails
    # calculate 80% of available threads, round down to nearest integer
    cpu_threads = max(1, math.floor(total_threads * 0.8))
    debug(f"\nusing {cpu_threads} CPU threads out of {total_threads} total")

    model = WhisperModel("turbo", device="cpu", compute_type="int8", cpu_threads=cpu_threads)
    segments, _ = model.transcribe(
        outputfile,
        initial_prompt="This is a conversation with an AI assistant named Eva.",
        beam_size=8,
        patience=1.0,
        language="en",
        condition_on_previous_text=True
    )

    result = " ".join(s.text for s in segments)
    stop_event_spin.set()
    thread_spin.join()
    print(f"\nUser said: {result}")
    print(f'{Bar("TRANSCRIBTER_END")}\n')
    if delete:
        os.remove(outputfile)
    return result

def is_assistant_called(text, names):
    text = text.strip().lower()
    for name in names :
        if text.startswith(name):
            return True 
    return False

def greeting(dir):
    greetings = os.listdir(dir)
    choosed = random.choice(greetings)
    selected =  f"{dir}/{choosed}"
    debug(f'Selected greeting: {selected}')
    return selected


def PlaySound(file):
    debug(f"Playing {file}")
    wave_obj = sa.WaveObject.from_wave_file(file)
    play_obj = wave_obj.play()
    play_obj.wait_done()

def endmsg(end_msg):
    print(f"{end_msg}\n{Bar(f'AI RESPONSE END')}\n")

def checkin(text, ls):
    for elem in ls :
        if elem in text:
            return True
    return  False 
# commands :
def open_search_in_browser(url, query):
    debug(f"Searching {query}")
    encoded_query = urllib.parse.quote_plus(query)
    url = f"{url}{encoded_query}"
    webbrowser.open(url)

def MusicControll(mode) :
    if mode:
        sb.check_output(['mpc', 'play'])
    else:
        sb.check_output(["mpc", "pause"])

def  cmdoutput(args):
    debug(f"command: {args}")
    return sb.check_output(args).decode("utf-8").replace("'", "").strip()

def AI_RESPONSE(question, model):
    print(Bar("AI RESPONSE"))
    try:
        assistant_names = [assistant_name.lower(), "iva", "eve", "evo", "ivo"]
        question = question.strip()
        quest_cmd = question.translate(str.maketrans('', '', string.punctuation)).lower()
        debug(f"question: {question}, quest_cmd: {quest_cmd}")

        # iva added here because sometimes Transcribter  return iva instead eva
        if is_assistant_called(question, assistant_names) :
            for name in assistant_names : 
                if name == quest_cmd  :
                    file = greeting("greetings")
                    if len(file) == 0 :
                        msg = "I’m listening Master. Don’t hesitat to ask "
                        endmsg(msg)
                        return msg, 1 

                    else :
                        msg = "Greeting -> |^w^| ->"
                        endmsg(msg)
                        PlaySound(file)
                        return "", 0 

            if "search for" in quest_cmd :
                query = question.rstrip(".!?").lower().strip().split("search for")[-1].strip()
                print(query)
                open_search_in_browser("https://duckduckgo.com/?t=ffab&q=", query)
                msg = f'All set! I’ve opened the results for "{query}" in your browser.'
                endmsg(msg)
                return msg, 1

            elif checkin(quest_cmd, ['play music', 'start music']):
                if "play" in quest_cmd:
                    msg = "Playing music"
                    PlaySound(f"{cstv.cmds_dir}/plm.wav")
                else:
                    msg = 'Starting music'
                    PlaySound(f"{cstv.cmds_dir}/stm.wav")

                endmsg(msg)
                MusicControll(1)
                return "", 0
        
            elif checkin(quest_cmd, ['stop music', 'pause music']):
                if "stop" in quest_cmd:
                    msg = "Stoping music"
                    PlaySound(f"{cstv.cmds_dir}/spm.wav")
                else:
                    msg = "Pausing music"
                    PlaySound(f"{cstv.cmds_dir}/psm.wav")

                endmsg(msg)
                MusicControll(0)
                return "", 0

            elif checkin(quest_cmd, ["show me the date", "what is todays date"]):
                cmd = cmdoutput(["date", "+'%A %d %B %Y'"])
                msg = f"Here is the date: {cmd}"
                endmsg(msg)
                return msg, 1

            elif checkin(quest_cmd, ['show me the time' ,'what is the time now']) :
                timeWarper = time.localtime()
                hour  = timeWarper.tm_hour
                APM = "AM" if hour > 0 and hour < 13 else "PM"
                # clock = f"{timeWarper.tm_hour} hour {timeWarper.tm_min} minute {timeWarper.tm_sec} seconds {APM}"
                clock = f"{timeWarper.tm_hour} hour, {timeWarper.tm_min} minute, {timeWarper.tm_sec} seconds {APM}"
                msg = f"Here is the time: {clock}"
                endmsg(msg)
                return msg, 1

            elif "show me the calendar" in quest_cmd :
                cmd = cmdoutput(["date", "+'%A %d %B %Y'"])
                cal = cmdoutput(['cal', '-Y'])
                msg_p1 = f"Here is the calander and today is {cmd}"
                msg_p2 = msg_p1 + f" : \n\n{cal}"
                endmsg(msg_p2)
                return msg_p1, 1

            elif "show me the system info" in quest_cmd:
                cmd = cmdoutput(["sh", "shell/sysfetch"])
                msg = f"Here is the system information:\n{cmd}"
                endmsg(msg)
                PlaySound(f"{cstv.cmds_dir}/sysinfo.wav")
                return "", 0

            elif checkin(quest_cmd, ['lock my laptop', 'lock my pc']):
                msg = "Your laptop is going to lock in 1 seconds"
                endmsg(msg)
                PlaySound(f"{cstv.cmds_dir}/lck.wav")
                time.sleep(0.5)
                cmdoutput(["physlock", "-d"])
                return "", 0 

        system_prompt = (
            f"{assistant_name} is a friendly and knowledgeable woman who helps with electronics, programming, and cybersecurity. "
            "She explains clearly and patiently, using simple language anyone can understand. "
            "Avoid markdown formatting, speaker labels, and emotional responses. "
            "Do not mention being an assistant or AI. Respond with confident, human-like expertise in plain, concise text."
        )


        stream = chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            stream=True
        )

        response = []
        for chunk in stream:
            content = chunk.get('message', {}).get('content', '')
            print(content, end='', flush=True)
            response.append(content)

        print(f"\n{Bar('AI RESPONSE END')}")
        text = ''.join(response)

        if "*" in text:
            text.replace("*", "")

        return text, 1

    except Exception as e:
        print(f"[ ERROR ] {e}")
        print("Exception type:", type(e).__name__)
        print("Exception message:", str(e))
        print("Full traceback:")
        traceback.print_exc()

        print(Bar('AI RESPONSE END'))
        return f"Sorry but something went wrong !! here is the following  error: {e}", 1


def TTS(data, outputfile, play=True):
    print(f'{Bar("TTS")}')
    print()
    tts(data).save(outputfile)
    if play:
        PlaySound(outputfile)
    
    print(f'{Bar("TTS END")}')
    os.remove(outputfile)


def main():
    global  assistant_name
    TestInputSound = False
    assistant_name = 'Eva'
    DisableErrorMsgs()
    # for models that have been tested 
    """
    tinydolphin: very fast response but less accurate
    gurubot/phi3-mini-abliterated: medium speed but accurate 
    huihui_ai/phi4-mini-abliterated: medium speed and accurate but best of all: uncensored (Default)
    gemma3: Slow but provide more accurate
    """
    # model = "gemma3"
    # model = "tinydolphin"
    model = "huihui_ai/phi4-mini-abliterated"
    output_wav = '.micro.wav'
    speech_wav = '.output.wav'
    Banner()
    print("\n[Click Enter to start recording...] ", end='')
    input()
    Record(output_wav, 1)

    if TestInputSound:
        data, sr = sf.read(output_wav)
        data = data * 1.5
        sd.play(data, sr)
        sd.wait()

    text = Transcribter(output_wav)
    # text = "Eva, lock my pc"
    response, run_tts = AI_RESPONSE(text, model)
    if run_tts:
        TTS(response, speech_wav)
    # input()
    

if __name__ == "__main__":
    while True:
        try:
            main()
        except KeyboardInterrupt :
            print("\nCtrl+C Ending AI assistant")
            os._exit(0)

