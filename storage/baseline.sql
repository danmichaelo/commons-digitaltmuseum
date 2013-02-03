CREATE TABLE files (
  institution TEXT NOT NULL,
  imageid TEXT NOT NULL,
  collection TEXT NOT NULL,
  first_revision INTEGER NOT NULL,
  upload_date INTEGER NOT NULL,
  uploader TEXT NOT NULL,
  filename TEXT NOT NULL,
  width INTEGER NOT NULL,
  height INTEGER NOT NULL,
  size INTEGER NOT NULL,
  author TEXT NOT NULL,
  source TEXT NOT NULL,
  date TEXT NOT NULL,
  description TEXT NOT NULL,
  revision INTEGER NOT NULL,
  PRIMARY KEY (filename)
);
CREATE INDEX institution_imageid ON files(institution,imageid);
CREATE UNIQUE INDEX uk_firstrev ON files(first_revision);
CREATE UNIQUE INDEX uk_rev ON files(revision);

