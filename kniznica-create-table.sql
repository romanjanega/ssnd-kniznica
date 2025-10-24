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