"""
Async subprocess test, wait for end of process

"""

import asyncio


async def _stream_subprocess(cmd):
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    p = await process.wait()
    print("p", p)  # return code (0 if ok)
    print("stdout:", (await process.stdout.read()).decode('utf8'))
    print("stderr:", (await process.stderr.read()).decode('utf8'))


def execute(cmd):
    loop = asyncio.get_event_loop()
    rc = loop.run_until_complete(
        _stream_subprocess(
            cmd
    ))
    loop.close()
    return rc


if __name__ == '__main__':
    print(execute(["bash", "-c", "echo stdout && sleep 1 && echo stderr 1>&2 && sleep 1 && echo done"]))