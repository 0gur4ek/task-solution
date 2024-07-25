# -*- coding: utf-8 -*-
import os
import re
import json
import argparse
import sys
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
from pathlib import Path

def DetectMissingText(original_file_name, audio_file_name):
    
    # Магические числа формата wav
    FRAME_RATE = 44100
    CHANNELS   = 1

    # Открытие оригинального файла и его обработка
    with open(original_file_name, "r", encoding="utf-8") as textfile:
        original_text = textfile.read()
        original_text = re.sub(r'[^\w\s]', '', original_text)

    # Подклюсение модели
    model  = Model("model-ru")
    record = KaldiRecognizer(model, FRAME_RATE)
    record.SetWords(True)

    # Предобработка аудио
    audio_result = AudioSegment.from_wav(audio_file_name)
    audio_result = audio_result.set_channels(CHANNELS)
    audio_result = audio_result.set_frame_rate(FRAME_RATE)
    
    record.AcceptWaveform(audio_result.raw_data)
    result      = record.Result()
    json_result = json.loads(result)

    # Массивы со словами
    wordbox_orig  = original_text.lower().split(" ")
    wordbox_audio = json_result["text"].replace('ё', 'e').split(" ")

    # Смотрим задержки по времени между словами
    time_delays_start = [i['start'] for i in json_result['result']]
    time_delays_end   = [i['end'] for i in json_result['result']][1:]
    time_delays_start = time_delays_start[:len(time_delays_start)-1]

    time_delays = [
        [
            time_delays_end[i] - time_delays_start[i]
        ]  
        for i in range(len(time_delays_start))
    ]

    # Средняя задержка по времени
    average_delay = [sum(d) / len(d) for d in zip(*time_delays)][0]

    solution_string = ""
    start_string    = ""
    goal_start      = 0
    goal_end        = 0

    # Поиск потеряшки
    for i in range(len(time_delays_start)):
        if time_delays_end[i] - time_delays_start[i] > average_delay*2:
            start_string = wordbox_audio[i]
            goal_start   = time_delays_start[i]
            goal_end     = time_delays_end[i]

    for i in wordbox_orig[wordbox_orig.index(start_string):]:
        if i not in wordbox_audio:
            solution_string += i + ' '

    #Вывод
    if solution_string != "":
        print("\nЕсть 'потеряшка'!")
        print("Скорее всего ее текст:", solution_string)
        print("Между", goal_start, "и", goal_end, "секундой")
    else:
        print("Все хорошо, 'потеряшек' нет")
    
    
    

def main():
    parser = argparse.ArgumentParser(description="Введите названия исходного файла и аудиофайла")
    
    # Добавление аргументов
    parser.add_argument('origname', type=str, help="Исходный файл")
    parser.add_argument('audioname', type=str, help="Аудиофайл")
    
    # Разбор аргументов
    args = parser.parse_args()
    
    # Доступ к аргументам
    origname  = args.origname
    audioname = args.audioname
    
    # Проверка значений
    if not isinstance(origname, str) and not isinstance(audioname, str):
        print("Введите пожалуйста строку")
    elif Path(origname).suffix != '.txt':
        print("Требуется расширение .txt для файов оригинального текста")
    elif Path(audioname).suffix != '.wav':
        print("Требуется расширение .wav для файов аудиодорожки")
    else:
        DetectMissingText(origname, audioname)
    



if __name__ == '__main__':
    if sys.version_info < (3, 6):
        sys.exit('Python 3.6 or later is required.\n')
    main()
    