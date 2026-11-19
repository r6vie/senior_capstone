import asyncio
import sys

from evals.librarian import main

asyncio.run(main(sys.argv[1:]))
