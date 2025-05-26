import re
from youtube_transcript_api import YouTubeTranscriptApi

def extract_video_id(url):
    """
    Извлекает video_id из URL видео YouTube
    """
    pattern = r"(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, url)
    if not match:
        raise ValueError("Не удалось извлечь video_id из URL.")
    return match.group(1)


def extract_youtube_video_data(url, lang='ru'):
    """
    Получает субтитры и название видео. Возвращает (title, transcript_text)
    """
    try:
        video_id = extract_video_id(url)

        # получаем субтитры
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
        full_text = "\n".join([entry['text'] for entry in transcript])

        return full_text
    except Exception as e:
        return "Видео YouTube"
