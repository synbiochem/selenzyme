# Docker file that installs docker container for Selenzyme
#
# build with: "sudo docker build -t selenzyme ."
FROM continuumio/anaconda3:5.0.1

# Install tools
<<<<<<< HEAD
RUN conda install -c conda-forge flask-restful=0.3.6 --no-update-dependencies
RUN conda install -c anaconda biopython=1.69
RUN conda install -c rdkit rdkit=2017.09.3.0
RUN conda install -c bioconda emboss=6.5.7
RUN conda install -c biobuilds t-coffee=11.00
=======
RUN conda install -c conda-forge flask-restful=0.3.6 \
  && conda install -c anaconda biopython=1.69 \
  && conda install -c rdkit rdkit=2017.09.3.0 \
  && conda install -c bioconda emboss=6.5.7 \
  && conda install -c biobuilds t-coffee=11.00
>>>>>>> 6b9d5730c91095d04c1b3440b493bf780cfdaff0

ENTRYPOINT ["python"]
CMD ["/selenzyme/selenzyPro/flaskform.py", "-uploaddir", "/selenzyme/selenzyPro/uploads", "-datadir", "/selenzyme/selenzyPro/data", "-logdir", "/selenzyme/selenzyPro/log"]

EXPOSE 5000
