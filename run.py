import asyncio
from pathlib import Path
import sys
from datetime import timedelta

from yapapi.log import enable_default_logger, log_summary, log_event_repr  # noqa
from yapapi.runner import Engine, Task, vm
from yapapi.runner.ctx import WorkContext
from datetime import timedelta

import utils


def write_hash(hash):
    with open("in.hash", "w") as f:
        f.write(hash)


def read_password(task_id):
    with open(f"outputs/out_{task_id}.txt", "r") as f:
        line = f.readline()

    if '?' in line:
        return line[2:].strip()

    return None


async def main(args):

    write_hash(args.hash)

    package = await vm.repo(
        image_hash='294668fd31f6535e65531fc4ea9d72e1377468f32ac8999f9cec89b3',
        min_mem_gib=1,
        min_storage_gib=2.0,
    )

    tasks: range = range(1, args.number_of_providers + 1)

    async def worker(ctx: WorkContext, tasks):
        async for task in tasks:
            ctx.send_file('in.hash', '/golem/work/in.hash')
            ctx.send_file('crack.sh', '/golem/work/crack.sh')
            ctx.run('touch', '/golem/work/out.txt')
            ctx.run('/bin/sh', '/golem/work/crack.sh', f'{task.data}', f'{args.number_of_providers}')
            log_file = f'logs/log_{task.data}.txt'
            ctx.download_file('/golem/work/log.txt', log_file)
            output_file = f'outputs/out_{task.data}.txt'
            ctx.download_file('/golem/work/out.txt', output_file)
            yield ctx.commit()
            task.accept_task(result=output_file)

    password = None

    async with Engine(
        package=package,
        max_workers=args.number_of_providers,
        budget=10.0,
        timeout=timedelta(minutes=10),
        subnet_tag=args.subnet_tag,
        event_emitter=log_summary(log_event_repr),
    ) as engine:

        async for task in engine.map(worker, [Task(data=task) for task in tasks]):
            print(f'\033[36;1mTask computed: {task}, result: {task.output}\033[0m')

            password = read_password(task.data)
            if password:
                break

    if password is None:
        print(f"{utils.TEXT_COLOR_RED}No password found{utils.TEXT_COLOR_DEFAULT}")
    else:
        print(
            f"{utils.TEXT_COLOR_GREEN}"
            f"Password found: {password}"
            f"{utils.TEXT_COLOR_DEFAULT}"
        )


if __name__ == "__main__":
    parser = utils.build_parser("john")

    parser.add_argument("--number-of-providers", dest="number_of_providers", type=int, default=3)
    parser.add_argument("hash")

    args = parser.parse_args()

    enable_default_logger(log_file=args.log_file)

    sys.stderr.write(
        f"Using subnet: {utils.TEXT_COLOR_YELLOW}{args.subnet_tag}{utils.TEXT_COLOR_DEFAULT}\n"
    )

    Path('logs').mkdir(parents=True, exist_ok=True)
    Path('logs').mkdir(parents=True, exist_ok=True)


    loop = asyncio.get_event_loop()
    task = loop.create_task(main(args))

    try:
        loop.run_until_complete(task)
    except (Exception, KeyboardInterrupt) as e:
        print(e)
        task.cancel()
        loop.run_until_complete(task)
