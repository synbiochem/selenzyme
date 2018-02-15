# Docker file that installs docker container for Selenzyme
#
# build with: "sudo docker build -t selenzyme ."
FROM continuumio/anaconda3:4.4.0

RUN ls -l

# Install rdkit
RUN conda install -c rdkit rdkit
RUN conda install -c conda-forge flask-restful
RUN conda install -c anaconda biopython
RUN conda install -c bioconda emboss
RUN conda install -c biobuilds t-coffee

RUN cd selenzyme
ENTRYPOINT ["python"]
CMD ["selenzyPro/flaskform.py", "-uploaddir", "selenzyPro/uploads", "-datadir", "selenzyPro/data", "-logdir", "selenzyPro/log"]

EXPOSE 5000
