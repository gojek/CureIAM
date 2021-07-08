venv:
	python3 -m venv ~/.venv/CureIAM
	echo . ~/.venv/CureIAM/bin/activate > venv

clean:
	find . -name "__pycache__" -exec rm -r {} +
	find . -name "*.pyc" -exec rm {} +
	rm -rf .coverage.* .coverage htmlcov build CureIAM.egg-info dist

