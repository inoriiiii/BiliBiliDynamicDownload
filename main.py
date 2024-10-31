import os
import sys
import argparse
import asyncio
import aiohttp
import bilibili_api

from bilibili_api import user

failed = []


async def download(session: aiohttp.ClientSession, url: str, path: str):
    try:
        async with session.get(url=url) as response:
            filename = url.split('/')[-1]
            with open(os.path.join(path, filename), 'wb') as f:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    f.write(chunk)
    except:
        if url not in failed:
            failed.append(url)


def dict2urls(data: dict):
    res = {"pics": []}
    for item in data["items"]:
        major = item["modules"]["module_dynamic"]["major"]
        if major and "opus" in major:
            res["pics"] += [pic["url"] for pic in major["opus"]["pics"]]
    return res


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('uid', nargs=1)
    parser.add_argument('--path', default='pics')
    args = parser.parse_args()
    u = user.User(uid=args.uid)
    path = os.path.join(args.path, args.uid)
    os.makedirs(path, exist_ok=True)
    offset = ""
    while True:
        res = await u.get_dynamics_new(offset)
        # with open(offset+".yaml", 'w', encoding='utf8') as f:
        #     yaml.dump(res, f, encoding='utf8', allow_unicode=True)

        if (not res["has_more"]):
            break
        offset = res["offset"]
        urls = dict2urls(res)["pics"]
        async with aiohttp.ClientSession() as session:
            tasks = [download(session=session, url=url, path=path)
                     for url in urls]
            await asyncio.gather(*tasks)

    print("----restart the failed pics----")
    async with aiohttp.ClientSession() as session:
        tasks = [download(session=session, url=url, path=path)
                 for url in failed]
        await asyncio.gather(*tasks)
    print("----donwnload finish----")
    print("----failed----")
    for url in failed:
        print(url)


if __name__ == "__main__":
    asyncio.run(main())
