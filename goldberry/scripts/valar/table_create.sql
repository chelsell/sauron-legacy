CREATE TABLE `dags_to_create` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `submission_hash` char(12) NOT NULL,
  `dag_created` tinyint(1) NOT NULL default 0,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_hash_hex` (`submission_hash`)
)