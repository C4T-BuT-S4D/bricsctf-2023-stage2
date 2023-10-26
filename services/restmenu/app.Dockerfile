FROM openjdk:21-slim-bullseye

WORKDIR /app/
COPY menuservice/ .
RUN  ./gradlew --no-daemon build

ENTRYPOINT ["java", "-jar", "build/libs/menuservice-all.jar"]