FROM openjdk:21-slim-bullseye

WORKDIR /app/
COPY renderer/ .
RUN ./gradlew --no-daemon build

ENTRYPOINT ["java", "-jar", "build/libs/renderer-0.0.1-SNAPSHOT.jar"]