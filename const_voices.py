import simpleaudio as sa
import os

from simpletts import tts

cmds_dir = 'cmds'
cmds = [
    ('plm','Playing music'),
    ('stm', 'Starting music'),
    ('psm', 'Pausing music'),
    ('spm', 'Stopping music'),
    ('sysinfo', 'Here is the system information'),
    ('lck', 'Your laptop is going to lock in 1 seconds')

]

greetings_dir = 'greetings'
greetings = [
    "Yes, Master? How can I help you today?",
    "I'm here, Master. What would you like me to do?",
    "At your service Master. Just tell me what you need.",
    "Hello, Master. I'm ready whenever you are.",
    "Right here Master. Please let me know how I can assist.",
    "Hello Master. I’m waiting for you… ready to give you all of my attention.",
    "I'm listenin Master. Please don’t hesitate to ask."
]

def main():
    if not os.path.exists(cmds_dir):
        os.mkdir(cmds_dir)

    for cmd in cmds:
        outputfile = f"{cmds_dir}/{cmd[0]}.wav"
        tts(cmd[1]).save(outputfile)
        wave_obj = sa.WaveObject.from_wave_file(outputfile)
        play_obj = wave_obj.play()
        play_obj.wait_done()


    if not os.path.exists(greetings_dir):
        os.mkdir(greetings_dir)

    for ind, grt in enumerate(greetings):
        outputfile = f"{greetings_dir}/grt_{ind}.wav"
        tts(grt).save(outputfile)
        wave_obj = sa.WaveObject.from_wave_file(outputfile)
        play_obj = wave_obj.play()
        play_obj.wait_done()

if __name__ == "__main__":
    main()
