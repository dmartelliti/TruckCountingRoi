import subprocess

url_1 = """https://rr6---sn-jup-x1xk.googlevideo.com/videoplayback?expire=1770144753&ei=ke-BaeinAqri-LAPvLWP8Qk&ip=2803%3A9800%3A902c%3A4b2b%3Ad419%3A17fe%3Ada6e%3A8821&id=o-AGylHrjLy0NY8v-Fuhn8gPfkqL1zjBlvwG3oh_DDyvqo&itag=399&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&cps=135&met=1770123153%2C&mh=y0&mm=31%2C29&mn=sn-jup-x1xk%2Csn-x1x7dn7z&ms=au%2Crdu&mv=m&mvi=6&pl=48&rms=au%2Cau&initcwndbps=1662500&bui=AW-iu_qOUUnGHys_MFPkBHuNLPTaH5kECk_hQHfyYpr-gSvgkOU7eXH0l7SXpm9Mrs2HUbrG47MaL8Co&spc=q5xjPKbh45jBTjJVu3qkc1HIhJc64A2nkabYoyAMiyUomdhTt8asKfLk-4IMsVp_&vprv=1&svpuc=1&mime=video%2Fmp4&rqh=1&gir=yes&clen=118098822&dur=1570.902&lmt=1765047202159784&mt=1770122755&fvip=1&keepalive=yes&fexp=51552689%2C51565116%2C51565681%2C51580968&c=ANDROID&txp=530G224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Cbui%2Cspc%2Cvprv%2Csvpuc%2Cmime%2Crqh%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJEij0EwRAIgOgBkPmV1-yeD3BT18eAq3vcfjn-Xr2qLeVTnBE2OlWwCID-kWHf7U_4r6561RAUe8JuG8zQFrXBSmvuAAuDzrBWl&lsparams=cps%2Cmet%2Cmh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Crms%2Cinitcwndbps&lsig=APaTxxMwRQIhAJcl4J1QW0ZNcWLqDDlXCEx4dJ75NLNdDvXhNnoTIkC7AiAyPXfd40oOb_191khWBxszSYYHnUDbTBYMbWi2TjNnEw%3D%3D
"""

url_2 = "https://worldcamnetwork.live/?utm_source=chatgpt.com"


def get_youtube_stream_url(url):
    """
    Usa yt-dlp para obtener el stream directo
    """
    command = [
        "yt-dlp",
        "-f", "best[ext=mp4]/best",
        "-g",
        url
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError("❌ Error obteniendo stream de YouTube")

    return result.stdout.strip()