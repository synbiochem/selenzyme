# Docker file that installs docker container for Selenzyme
#
# build with: "sudo docker build -t selenzyme ."
FROM sbc/selenzybase

ENTRYPOINT ["python"]
CMD ["/selenzyme/selenzyPro/flaskform.py", "-uploaddir", "/selenzyme/selenzyPro/uploads", "-datadir", "/selenzyme/selenzyPro/data", "-logdir", "/selenzyme/selenzyPro/log"]

EXPOSE 5000
