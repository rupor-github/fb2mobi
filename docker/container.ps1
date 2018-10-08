docker build --squash -t fb2mobi:latest .. -f .\Dockerfile.build | Tee-Object -FilePath "..\..\all.log"

# docker save -o ..\..\fb2mobi.tar fb2mobi
# docker load -i ..\..\fb2mobi.tar

# docker run --name fb2mobi -v E:/projects/books/fb2mobi:/root/result -it fb2mobi:latest
