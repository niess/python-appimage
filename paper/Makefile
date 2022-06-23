paper.pdf: paper.md paper.bib
	docker run --rm \
	           --volume ${PWD}:/data \
	           --user $(id -u):$(id -g) \
	           --env JOURNAL=joss \
	           openjournals/inara \
	           -o pdf \
	           /data/paper.md


.PHONY: clean
clean:
	rm -f paper.pdf
