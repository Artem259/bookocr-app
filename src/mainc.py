import argparse
import concurrent.futures
import multiprocessing
import os.path
import sys
import time
from pathlib import Path
from bookocr.ocr import Ocr
from bookocr.config import OcrConfig
from bookocr.stats_config import OcrStatsConfig


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=str, help="Path to the source image or folder")
    parser.add_argument("target_folder", type=str, help="Path to the target folder")
    parser.add_argument("--config", type=str, help="Path to the config .json file")
    parser.add_argument("--sconfig", type=str, help="Path to the stats config .json file")
    parser.add_argument("--s", action="store_true", help="Save stats")
    parser.add_argument("--m", action="store_true", help="Use multiprocessing")

    args = parser.parse_args()
    return args


def get_image_paths(path):
    if os.path.isfile(path):
        return [str(path)]
    elif os.path.isdir(path):
        image_paths = [os.path.join(path, file_name) for file_name in os.listdir(path)]
        image_paths = [file_path for file_path in image_paths if os.path.isfile(file_path)]
        return image_paths
    return []


def process_image(image_path):
    args = parse_arguments()
    start_time = time.time()

    config = OcrConfig()
    stats_config = OcrStatsConfig()
    if args.config is not None and os.path.exists(args.config):
        config = OcrConfig.from_json_file(Path(args.config))
    if args.sconfig is not None and os.path.exists(args.sconfig):
        stats_config = OcrStatsConfig.from_json_file(Path(args.sconfig))

    image_name = os.path.basename(image_path)
    target_folder = Path(args.target_folder) / image_name
    if args.s:
        stats_config.set_enabled_true(target_folder)
    ocr = Ocr(config, stats_config)

    try:
        ocr.image_ocr(image_path)
    except FileNotFoundError:
        print(f' > {image_name}:   Not an image')
        return

    if not args.s:
        if not target_folder.exists():
            target_folder.mkdir(parents=True)
        result = ocr.get_data_as_text()
        with open(target_folder / "output.txt", "w") as f:
            f.write(result)
    res_time = time.time() - start_time
    print(f' > {image_name}:   {round(res_time, 3)} sec')


if __name__ == '__main__':
    multiprocessing.freeze_support()
    args = parse_arguments()
    images = get_image_paths(Path(args.source))

    if args.config is not None and not os.path.exists(args.config):
        print("Config file not found.")
        args.config = None

    if args.sconfig is not None and not os.path.exists(args.sconfig):
        print("Stats config file not found.")
        args.sconfig = None

    if not images:
        print("Source path not found.")
        sys.exit()
    start_time = time.perf_counter()
    if args.m:
        with concurrent.futures.ProcessPoolExecutor() as exe:
            exe.map(process_image, images)
    else:
        for i in images:
            process_image(i)
    res_time = time.perf_counter() - start_time
    print(f'Total time:   {round(res_time, 3)} sec')
