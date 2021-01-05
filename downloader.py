import sys
import os
import urllib.request, urllib.parse, urllib.error
import threading
from queue import Queue

class DownloadThread(threading.Thread):
    def __init__(self, queue, destfolder):
        super(DownloadThread, self).__init__()
        self.queue = queue
        self.destfolder = destfolder
        self.daemon = True

    def run(self):
        while True:
            url = self.queue.get()
            try:
                self.download_url(url)
            except Exception as e:
                print("   Error: %s"%e)
            self.queue.task_done()

    def download_url(self, url):
        # change it to a different way if you require
        name = url.split('/')[-1]
        dest = os.path.join(self.destfolder, name)
        print("[%s] Downloading %s -> %s"%(self.ident, url, dest))
        urllib.request.urlretrieve(url, dest)

def download(urls, destfolder, numthreads=4):
    queue = Queue()
    for url in urls:
        queue.put(url)

    for i in range(numthreads):
        t = DownloadThread(queue, destfolder)
        t.start()

    queue.join()

if __name__ == "__main__":
    download(sys.argv[1:], "/tmp")