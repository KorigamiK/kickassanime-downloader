import asyncio
from asyncio.subprocess import PIPE
from time import time
from types import coroutine


def timer(function):
    async def wrapped_func(*args, **kwargs):
        s = time()
        res = await function(*args, **kwargs)
        print(f"{function.__name__} took {time()-s} seconds")
        return res

    return wrapped_func


async def async_subprocess(
    *cmd_args,
    std_inputs: list = [],
    loop: asyncio.AbstractEventLoop = None,
    description="Process",
):
    process = await asyncio.create_subprocess_exec(
        *cmd_args, stderr=PIPE, stdin=PIPE, loop=loop, stdout=PIPE
    )

    async def _read_stream(stream: asyncio.StreamReader, stream_type: str):
        """ Breaks if an empty line is the output of error """
        while True:
            line = await stream.readline()
            # await asyncio.sleep(.1)
            if line:
                print(f"[{description}] {stream_type}: {line.decode('utf-8').strip()}")
            else:
                break

    async def _write_stream(stream: asyncio.StreamWriter, inputs: list):
        """waits 1 sec for each input"""
        for input in inputs:
            await asyncio.sleep(1)
            buf = f"{input}\n".encode()
            print(f"[{description}] stdin: {input}")

            stream.write(buf)
            await stream.drain()

    stderr_stream = process.stderr
    stdout_stream = process.stdout
    stdin_stream = process.stdin
    try:
        await asyncio.gather(
            _read_stream(stdout_stream, "stdout"),
            _read_stream(stderr_stream, "stderr"),
            _write_stream(stdin_stream, std_inputs),
        )
    except Exception as e:
        print(f"[{description}] ERROR: {e}")
    return await process.wait()

# @timer
async def gather_limitter(*args: coroutine, max=5):
    start = 0
    while start<len(args):        
        iterable_range = range(start, start + max) if len(args) >= start+max else range(start, len(args))
        tasks = [args[i] for i in iterable_range]
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f'Completed {len(tasks) + start} of {len(args)} tasks \n')
        start += max

if __name__=='__main__':
    asyncio.run(gather_limitter(*[asyncio.sleep(2) for _ in range(9)], max=2))