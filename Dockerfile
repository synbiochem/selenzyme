# Docker file that installs docker container for Selenzy
#
# build with: "sudo docker build -t selenzy ."

FROM continuumio/anaconda3 

# Install rdkit
RUN conda install -c rdkit rdkit
RUN conda install -c conda-forge flask-restful
RUN conda install -c anaconda biopython
RUN conda install -c bioconda emboss
RUN conda install -c biobuilds t-coffee

# To be replace by a git clone
RUN wget http://130.88.113.226/selenzy/selenzy.tar.gz
RUN tar -xzvf selenzy.tar.gz

ENTRYPOINT ["python"]

CMD ["/selenzyPro/flaskform.py", "-uploaddir", "/selenzyPro/uploads", "-datadir", "/selenzyPro/data", "-logdir", "/selenzyPro/log"]

EXPOSE 5000