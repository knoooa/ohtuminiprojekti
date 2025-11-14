CREATE TABLE todos (
  id SERIAL PRIMARY KEY, 
  content TEXT NOT NULL,
  done BOOLEAN DEFAULT FALSE
);

CREATE TABLE book (
  id SERIAL PRIMARY KEY,
  title TEXT,
  author TEXT,
  year INTEGER,
  publisher TEXT,
  address TEXT
)