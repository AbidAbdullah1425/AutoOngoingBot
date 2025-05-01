import aiohttp

HF_URL = "https://abidabdullah199-Compressor.hf.space/"

async def send_to_huggingface(title, torrent_link):
    async with aiohttp.ClientSession() as session:
        data = {
            "title": title,
            "torrent_link": torrent_link,
            "crf": 26,
            "preset": "ultrafast"
        }
        try:
            async with session.post(HF_URL, data=data) as resp:
                res = await resp.json()
                print("HuggingFace response:", res)
                return res
        except Exception as e:
            print("Error sending to HF:", str(e))
            return {"status": "failed", "error": str(e)}