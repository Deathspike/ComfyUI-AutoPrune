from os import cpu_count, path

from folder_paths import get_output_directory

from .modules.prune import Prune

output_directory = get_output_directory()
pruned_directory = path.join(output_directory, "autoprune")
Prune(output_directory, pruned_directory, cpu_count() or 1)
