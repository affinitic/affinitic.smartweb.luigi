run:
	bin/luigi --module src.main Start --local-scheduler 

run-test :
	bin/luigi --module src.main Start --path "./data/test" --local-scheduler 

run-novac :
	LUIGI_CONFIG_PATH=./novac.cfg bin/luigi --module src.main Start --path "./data/novac" --local-scheduler 