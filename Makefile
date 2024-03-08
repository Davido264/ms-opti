# Tarea por defecto: run
.DEFAULT_GOAL := run

# Tarea setup: Instalar dependencias
setup:
	python -m pip install -e .

data: generate_dataset split_ds

generate_dataset:
	python scripts/generate_dataset

split_ds:
	python scripts/split_ds

run:
	python -m msopti
