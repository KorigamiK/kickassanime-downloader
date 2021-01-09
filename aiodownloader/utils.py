import functools
import asyncio
import copy
from typing import List, Optional, Coroutine

from tqdm import tqdm

# Typing imports
if False:
    from . import downloader


def pretty_tqdm(size: int, name: str):
    """Returns a tqdm pbar with some predefined options"""
    return tqdm(total=size, desc=name, unit_scale=True, unit='B')

async def progress_bar(job: 'downloader.DownloadJob') -> None:
    """
    Creates a tqdm progress bar for the given job. Updating it asynchronously every half a sec
    according to how much the job has advanced since the last update.
    
    :param job: download job that will have a progress bar
    """
    job_size = await job.get_size()
    pbar = pretty_tqdm(size=job_size, name=job.file_name)

    last_progress = 0
    while not job.completed:
        pbar.update(job.progress - last_progress)
        # We copy the progress into the last progress.
        last_progress = copy.copy(job.progress)
        await asyncio.sleep(0.5)

async def multi_progress_bar(jobs: List['downloader.DownloadJob']) -> None:
    """
    Creates one tqdm progress bar for every download job and updates all of them asynchronously 
    every sec according to how much the job has advanced since the last update.

    :param jobs: list of download jobs that will have a progress bar 
    :return: 
    """
    # Getting the job sizes to create the tqdm pbars
    jobs_done, _ = await asyncio.wait([job.get_size() for job in jobs])
    job_sizes = [done.result() for done in jobs_done]

    pbars = [pretty_tqdm(job_size, job.file_name) for job_size, job in zip(job_sizes, jobs)]

    # List to store the last seen progress from the jobs.
    last_progresses = [0] * len(jobs)

    uncompleted_jobs = True
    while uncompleted_jobs:
        uncompleted_jobs = False

        new_progresses = []
        for pbar, job, last_progress in zip(pbars, jobs, last_progresses):
            if not job.completed:
                # Updating the pbar with how much the job has advanced since the last update
                pbar.update(job.progress - last_progress)
                new_progresses.append(job.progress)
                uncompleted_jobs = True

        last_progresses = new_progresses
        await asyncio.sleep(0.5)


def make_sync(couroutine: [Coroutine, asyncio.Future], loop: Optional[asyncio.BaseEventLoop]):
    """
    Wraps a couroutine to work synchronously. 
    
    :param couroutine: the coroutine to be wrapped
    :param loop: A asyncio event loop
    :return: 
    """
    loop = loop or asyncio.get_event_loop()

    @functools.wraps(couroutine)
    def wrapper(*args, **kwargs):
        return loop.run_until_complete(couroutine(*args, **kwargs))

    return wrapper







