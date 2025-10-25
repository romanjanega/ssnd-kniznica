DROP TABLE IF EXISTS dielo;
DROP TABLE IF EXISTS autor;

CREATE TABLE autor
(
  id INT NOT NULL,
  meno VARCHAR(100),
  priezvisko VARCHAR(50) NOT NULL,
  narodenie DATE,
  umrtie DATE,
  ol_key CHAR(10),
  PRIMARY KEY (id),
  UNIQUE (ol_key)
);

CREATE TABLE dielo
(
  id INT NOT NULL,
  nazov VARCHAR(200) NOT NULL,
  ol_key CHAR(10),
  autor_id INT NOT NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (autor_id) REFERENCES autor(id),
  UNIQUE (ol_key)
   UNIQUE (nazov, autor_id)
);