/*
Sample Insertion SQL Queries to populate test db. Make sure unique keys are different for the VALUES.
*/


-- Host: 127.0.0.1    Database: valartest
-- ------------------------------------------------------

SET FOREIGN_KEY_CHECKS=0;

DROP DATABASE IF EXISTS valartest;
CREATE DATABASE valartest CHARACTER SET = 'utf8mb4' COLLATE 'utf8mb4_unicode_520_ci';
DROP USER IF EXISTS 'kaletest'@'localhost';
USE valartest;
CREATE USER 'kaletest'@'localhost' IDENTIFIED BY 'kale123';
GRANT SELECT, INSERT, UPDATE, DELETE ON valartest.* TO 'kaletest'@'localhost';


--
-- Table structure for table `annotations`
--

CREATE TABLE `annotations` (
  `id` mediumint(8) unsigned not null auto_increment,
  `name` varchar(255) default null,
  `value` varchar(255) default null,
  `level` enum(
      '0:good', '1:note', '2:caution', '3:warning', '4:danger', '9:deleted', 'to_fix', 'fixed'
   ) not null default '1:note',
  `run_id` mediumint(8) unsigned default null,
  `submission_id` mediumint(8) unsigned default null,
  `well_id` mediumint(8) unsigned default null,
  `assay_id` smallint(5) unsigned default null,
  `annotator_id` smallint(5) unsigned not null,
  `description` mediumtext default null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `run_id` (`run_id`),
  KEY `well_id` (`well_id`),
  KEY `assay_id` (`assay_id`),
  KEY `annotator_id` (`annotator_id`),
  KEY `level` (`level`),
  KEY `name` (`name`),
  KEY `submission_id` (`submission_id`),
  KEY `value` (`value`),
  CONSTRAINT `annotation_to_run` FOREIGN KEY (`run_id`) REFERENCES `runs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `annotation_to_assay` FOREIGN KEY (`assay_id`) REFERENCES `assays` (`id`) ON DELETE CASCADE,
  CONSTRAINT `annotation_to_person` FOREIGN KEY (`annotator_id`) REFERENCES `users` (`id`),
  CONSTRAINT `annotation_to_submission` FOREIGN KEY (`submission_id`) REFERENCES `submissions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `annotation_to_well` FOREIGN KEY (`well_id`) REFERENCES `wells` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `api_keys`
--

CREATE TABLE `api_keys` (
  `id` tinyint(3) unsigned not null auto_increment,
  `name` varchar(100) not null,
  `value` varchar(255) not null,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `assay_params`
--

CREATE TABLE `assay_params` (
  `id` smallint(5) unsigned not null auto_increment,
  `assay_id` smallint(5) unsigned not null,
  `name` varchar(30) CHARACTER SET latin1 not null,
  `value` double not null,
  PRIMARY KEY (`id`),
  UNIQUE KEY `assay_and_name_unique` (`name`, `assay_id`),
  KEY `assay_id` (`assay_id`),
  KEY `value` (`value`),
  CONSTRAINT `assay_param_to_assay` FOREIGN KEY (`assay_id`) REFERENCES `assays` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `assay_positions`
--

CREATE TABLE `assay_positions` (
  `id` smallint(5) unsigned not null auto_increment,
  `battery_id` smallint(5) unsigned not null,
  `assay_id` smallint(5) unsigned not null,
  `start` int(10) unsigned not null,
  PRIMARY KEY (`id`),
  UNIQUE KEY `battery_assay_start_unique` (`battery_id`, `assay_id`, `start`),
  KEY `battery_id` (`battery_id`),
  KEY `assay_id` (`assay_id`),
  KEY `start` (`start`),
  CONSTRAINT `assay_position_to_assay` FOREIGN KEY (`assay_id`) REFERENCES `assays` (`id`),
  CONSTRAINT `assay_position_to_battery` FOREIGN KEY (`battery_id`) REFERENCES `batteries` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `assays`
--

CREATE TABLE `assays` (
  `id` smallint(5) unsigned not null auto_increment,
  `name` varchar(250) not null,
  `description` varchar(10000) default null,
  `length` int(10) unsigned not null,
  `hidden` bool not null default 0,
  `template_assay_id` smallint(5) unsigned default null,
  `frames_sha1` binary(20) not null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_frames_sha1_unique` (`name`, `frames_sha1`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `name` (`name`),
  KEY `hash` (`frames_sha1`) USING BTREE,
  KEY `template_assay_id` (`template_assay_id`),
  CONSTRAINT `assay_to_template_assay` FOREIGN KEY (`template_assay_id`) REFERENCES `template_assays` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `audio_files`
--

CREATE TABLE `audio_files` (
  `id` smallint(5) unsigned not null auto_increment,
  `filename` varchar(100) not null,
  `notes` varchar(250) default null,
  `n_seconds` double unsigned not null,
  `data` mediumblob not null,
  `sha1` binary(20) not null,
  `creator_id` smallint(5) unsigned default null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `filename_unique` (`filename`),
  UNIQUE KEY `sha1_unique` (`sha1`),
  KEY `creator_id` (`creator_id`),
  CONSTRAINT `audio_file_to_user` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `batch_annotations`
--

CREATE TABLE `batch_annotations` (
  `id` int(10) unsigned not null auto_increment,
  `batch_id` mediumint(8) unsigned not null,
  `level` enum(
      '0:good', '1:note', '2:caution', '3:warning', '4:danger', '9:deleted'
   ) COLLATE utf8mb4_unicode_ci not null default '1:note',
  `name` varchar(50) COLLATE utf8mb4_unicode_ci default null,
  `value` varchar(200) COLLATE utf8mb4_unicode_ci default null,
  `description` varchar(200) COLLATE utf8mb4_unicode_ci default null,
  `annotator_id` smallint(5) unsigned not null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `batch_id` (`batch_id`),
  KEY `annotator_id` (`annotator_id`),
  KEY `level` (`level`),
  KEY `name` (`name`),
  KEY `value` (`value`),
  CONSTRAINT `batch_annotation_to_batch` FOREIGN KEY (`batch_id`) REFERENCES `batches` (`id`) ON DELETE CASCADE,
  CONSTRAINT `batch_annotation_to_user` FOREIGN KEY (`annotator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


--
-- Table structure for table `batch_labels`
--

CREATE TABLE `batch_labels` (
  `id` mediumint(8) unsigned not null auto_increment,
  `batch_id` mediumint(8) unsigned not null,
  `ref_id` smallint(5) unsigned not null,
  `name` varchar(250) not null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `batch_name` (`name`),
  KEY `batch_ref` (`ref_id`),
  KEY `batch_id` (`batch_id`),
  CONSTRAINT `batch_id_to_batch` FOREIGN KEY (`batch_id`) REFERENCES `batches` (`id`) ON DELETE CASCADE,
  CONSTRAINT `batch_label_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `batches`
--

CREATE TABLE `batches` (
  `id` mediumint(8) unsigned not null auto_increment,
  `lookup_hash` varchar(14) not null,
  `tag` varchar(100) default null,
  `compound_id` mediumint(8) unsigned default null,
  `made_from_id` mediumint(8) unsigned default null,
  `supplier_id` smallint(5) unsigned default null,
  `ref_id` smallint(5) unsigned default null,
  `legacy_internal_id` varchar(255) default null,
  `location_id` smallint(5) unsigned default null,
  `box_number` smallint(5) unsigned default null,
  `well_number` smallint(5) unsigned default null,
  `location_note` varchar(20) default null,
  `amount` varchar(100) default null,
  `concentration_millimolar` double unsigned default null,
  `solvent_id` mediumint(8) unsigned default null,
  `molecular_weight` double unsigned default null,
  `supplier_catalog_number` varchar(20) default null,
  `person_ordered` smallint(5) unsigned default null,
  `date_ordered` date default null,
  `notes` text default null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `lookup_hash_unique` (`lookup_hash`),
  UNIQUE KEY `box_well_unique` (`box_number`, `well_number`),
  UNIQUE KEY `tag_unique` (`tag`),
  KEY `compound_id` (`compound_id`),
  KEY `solvent_id` (`solvent_id`),
  KEY `legacy_internal_id` (`legacy_internal_id`) USING BTREE,
  KEY `ref_id` (`ref_id`),
  KEY `person_ordered` (`person_ordered`),
  KEY `supplier_id` (`supplier_id`),
  KEY `date_ordered` (`date_ordered`),
  KEY `box_number` (`box_number`),
  KEY `well_number` (`well_number`),
  KEY `made_from_id` (`made_from_id`),
  KEY `location_id` (`location_id`),
  CONSTRAINT `batch_to_batch` FOREIGN KEY (`made_from_id`) REFERENCES `batches` (`id`),
  CONSTRAINT `batch_to_location` FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`),
  CONSTRAINT `batch_to_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`),
  CONSTRAINT `batch_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `batch_to_solvent` FOREIGN KEY (`solvent_id`) REFERENCES `compounds` (`id`),
  CONSTRAINT `batch_to_user` FOREIGN KEY (`person_ordered`) REFERENCES `users` (`id`),
  CONSTRAINT `batch_to_compound` FOREIGN KEY (`compound_id`) REFERENCES `compounds` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `batteries`
--

CREATE TABLE `batteries` (
  `id` smallint(5) unsigned not null auto_increment,
  `name` varchar(100) not null,
  `description` varchar(10000) default null,
  `length` int(10) unsigned not null,
  `author_id` smallint(5) unsigned default null,
  `template_id` smallint(5) unsigned default null,
  `hidden` bool not null default 0,
  `notes` TEXT default null,
  `assays_sha1` binary(20) not null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `creator_id` (`author_id`),
  KEY `battery_to_template` (`template_id`),
  KEY `length` (`length`),
  KEY `assays_sha1` (`assays_sha1`),
  CONSTRAINT `battery_to_user` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `compound_labels`
--

CREATE TABLE `compound_labels` (
  `id` mediumint(8) unsigned not null auto_increment,
  `compound_id` mediumint(8) unsigned not null,
  `name` varchar(1000) not null,
  `ref_id` smallint(5) unsigned not null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `compound_id` (`compound_id`),
  KEY `ref_id` (`ref_id`),
  CONSTRAINT `compound_label_to_compound` FOREIGN KEY (`compound_id`) REFERENCES `compounds` (`id`) ON DELETE CASCADE,
  CONSTRAINT `compound_label_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `compounds`
--

CREATE TABLE `compounds` (
  `id` mediumint(8) unsigned not null auto_increment,
  `inchi` varchar(2000) not null,
  `inchikey` char(27) not null,
  `inchikey_connectivity` char(14) not null,
  `chembl_id` varchar(20) default null,
  `chemspider_id` int(10) unsigned default null,
  `smiles` varchar(2000) default null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `inchikey` (`inchikey`) USING BTREE,
  KEY `inchikey_connectivity` (`inchikey_connectivity`),
  KEY `chembl_id` (`chembl_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `config_files`
--

CREATE TABLE `config_files` (
  `id` smallint(5) unsigned not null auto_increment,
  `toml_text` mediumtext not null,
  `text_sha1` binary(20) not null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `text_sha1_unique` (`text_sha1`),
  KEY `text_sha1` (`text_sha1`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `control_types`
--

CREATE TABLE `control_types` (
  `id` tinyint(3) unsigned not null auto_increment,
  `name` varchar(100) not null,
  `description` varchar(250) not null,
  `positive` bool not null,
  `drug_related` bool not null default 1,
  `genetics_related` bool not null,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `name` (`name`),
  KEY `positive` (`positive`),
  KEY `drug_related` (`drug_related`),
  KEY `genetics_related` (`genetics_related`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `experiment_tags`
--

CREATE TABLE `experiment_tags` (
  `id` mediumint(8) unsigned not null auto_increment,
  `experiment_id` smallint(5) unsigned not null,
  `name` varchar(100) not null,
  `value` varchar(255) not null,
  `ref_id` smallint(5) unsigned not null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `exp_tag_unique` (`experiment_id`, `name`),
  KEY `ref_id` (`ref_id`),
  CONSTRAINT `experiment_tag_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `tag_to_experiment` FOREIGN KEY (`experiment_id`) REFERENCES `experiments` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `experiments`
--

CREATE TABLE `experiments` (
  `id` smallint(5) unsigned not null auto_increment,
  `name` varchar(200) not null,
  `description` varchar(10000) default null,
  `creator_id` smallint(5) unsigned not null,
  `project_id` smallint(5) unsigned not null,
  `battery_id` smallint(5) unsigned not null,
  `template_plate_id` smallint(5) unsigned default null,
  `transfer_plate_id` smallint(5) unsigned default null,
  `default_acclimation_sec` smallint(5) unsigned not null,
  `notes` text default null,
  `active` bool not null default 1,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `battery_id` (`battery_id`),
  KEY `project_id` (`project_id`),
  KEY `template_plate_id` (`template_plate_id`),
  KEY `transfer_plate_id` (`transfer_plate_id`),
  KEY `creator_id` (`creator_id`),
  CONSTRAINT `experiment_to_transfer_plate` FOREIGN KEY (`transfer_plate_id`) REFERENCES `transfer_plates` (`id`),
  CONSTRAINT `experiment_to_user` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`),
  CONSTRAINT `project_to_battery` FOREIGN KEY (`battery_id`) REFERENCES `batteries` (`id`),
  CONSTRAINT `project_to_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `project_to_template_plate` FOREIGN KEY (`template_plate_id`) REFERENCES `template_plates` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `features`
--

CREATE TABLE `features` (
  `id` tinyint(3) unsigned not null auto_increment,
  `name` varchar(50) not null,
  `description` varchar(250) not null,
  `dimensions` varchar(20) not null,
  `data_type` enum(
      'byte', 'short', 'int',
      'float', 'double',
      'unsigned_byte', 'unsigned_short', 'unsigned_int', 'unsigned_float', 'unsigned_double',
      'utf8_char'
) not null default 'float',
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `genetic_variants`
--

CREATE TABLE `genetic_variants` (
  `id` mediumint(8) unsigned not null auto_increment,
  `name` varchar(250) not null,
  `mother_id` mediumint(8) unsigned default null,
  `father_id` mediumint(8) unsigned default null,
  `lineage_type` enum('injection', 'cross', 'selection', 'wild-type') default null,
  `date_created` date default null,
  `notes` text default null,
  `creator_id` smallint(5) unsigned not null,
  `fully_annotated` bool not null default 0,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `mother_id` (`mother_id`),
  KEY `father_id` (`father_id`),
  KEY `creator_id` (`creator_id`),
  KEY `lineage_type` (`lineage_type`),
  CONSTRAINT `variant_to_father` FOREIGN KEY (`father_id`) REFERENCES `genetic_variants` (`id`),
  CONSTRAINT `variant_to_mother` FOREIGN KEY (`mother_id`) REFERENCES `genetic_variants` (`id`),
  CONSTRAINT `variant_to_user` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `locations`
--

CREATE TABLE `locations` (
  `id` smallint(5) unsigned not null auto_increment,
  `name` varchar(100) not null,
  `description` varchar(250) not null default '',
  `purpose` varchar(250) not null default '',
  `part_of` smallint(5) unsigned default null,
  `active` bool not null default 1,
  `temporary` bool not null default 0,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `part_of` (`part_of`),
  CONSTRAINT `location_to_location` FOREIGN KEY (`part_of`) REFERENCES `locations` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `log_files`
--

CREATE TABLE `log_files` (
  `id` smallint(5) unsigned not null auto_increment,
  `run_id` mediumint(8) unsigned not null,
  `text` mediumtext not null,
  `text_sha1` binary(20) not null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `text_sha1` (`text_sha1`),
  KEY `run_id` (`run_id`),
  CONSTRAINT `log_file_to_run` FOREIGN KEY (`run_id`) REFERENCES `runs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `plate_types`
--

CREATE TABLE `plate_types` (
  `id` tinyint(3) unsigned not null auto_increment,
  `name` varchar(100) default null,
  `supplier_id` smallint(5) unsigned default null,
  `part_number` varchar(100) default null,
  `n_rows` smallint(5) unsigned not null,
  `n_columns` smallint(5) unsigned not null,
  `well_shape` enum('round', 'square', 'rectangular') not null,
  `opacity` enum('opaque', 'transparent') not null,
  PRIMARY KEY (`id`),
  KEY `n_rows` (`n_rows`, `n_columns`),
  KEY `part_number` (`part_number`),
  KEY `plate_type_to_supplier` (`supplier_id`),
  CONSTRAINT `plate_type_to_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `plates`
--

CREATE TABLE `plates` (
  `id` smallint(5) unsigned not null auto_increment,
  `plate_type_id` tinyint(3) unsigned default null,
  `person_plated_id` smallint(5) unsigned not null,
  `datetime_plated` datetime default null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `datetime_plated` (`datetime_plated`),
  KEY `plate_type_id` (`plate_type_id`),
  KEY person_plated_id (`person_plated_id`),
  CONSTRAINT `plate_to_plate_type` FOREIGN KEY (`plate_type_id`) REFERENCES `plate_types` (`id`),
  CONSTRAINT `plate_to_user` FOREIGN KEY (`person_plated_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `project_tags`
--

CREATE TABLE `project_tags` (
  `id` mediumint(8) unsigned not null auto_increment,
  `project_id` smallint(5) unsigned not null,
  `name` varchar(100) not null,
  `value` varchar(255) not null,
  `ref_id` smallint(5) unsigned not null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `project_tag_unique` (`project_id`, `name`),
  KEY `ref_id` (`ref_id`),
  CONSTRAINT `project_tag_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `tag_to_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `project_types`
--

CREATE TABLE `project_types` (
  `id` tinyint(3) unsigned not null auto_increment,
  `name` varchar(50) not null,
  `description` text not null,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `refs`
--

CREATE TABLE `refs` (
  `id` smallint(5) unsigned not null auto_increment,
  `name` varchar(50) not null,
  `datetime_downloaded` datetime default null,
  `external_version` varchar(50) default null,
  `description` varchar(250) default null,
  `url` varchar(100) default null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `url` (`url`),
  KEY `name` (`name`),
  KEY `external_version` (`external_version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `rois`
--

CREATE TABLE `rois` (
  `id` int(10) unsigned not null auto_increment,
  `well_id` mediumint(8) unsigned not null,
  `y0` smallint(6) not null,
  `x0` smallint(6) not null,
  `y1` smallint(6) not null,
  `x1` smallint(6) not null,
  `ref_id` smallint(5) unsigned not null,
  PRIMARY KEY (`id`),
  KEY `well_id` (`well_id`),
  KEY `ref_id` (`ref_id`),
  CONSTRAINT `roi_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `roi_to_well` FOREIGN KEY (`well_id`) REFERENCES `wells` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `run_tags`
--

CREATE TABLE `run_tags` (
  `id` mediumint(8) unsigned not null auto_increment,
  `run_id` mediumint(8) unsigned not null,
  `name` varchar(100) not null,
  `value` varchar(10000) not null,
  PRIMARY KEY (`id`),
  UNIQUE KEY `run_name_unique` (`run_id`, `name`),
  CONSTRAINT `run_tag_to_run` FOREIGN KEY (`run_id`) REFERENCES `runs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `runs`
--

CREATE TABLE `runs` (
  `id` mediumint(8) unsigned not null auto_increment,
  `experiment_id` smallint(5) unsigned not null,
  `plate_id` smallint(5) unsigned not null,
  `description` varchar(200) not null,
  `experimentalist_id` smallint(5) unsigned not null,
  `submission_id` mediumint(8) unsigned default null,
  `datetime_run` datetime not null,
  `datetime_dosed` datetime default null,
  `name` varchar(100) default null,
  `tag` varchar(100) not null default '',
  `sauron_config_id` smallint(5) unsigned not null,
  `config_file_id` smallint(5) unsigned default null,
  `incubation_min` mediumint(9) default null,
  `acclimation_sec` int(10) unsigned default null,
  `notes` text default null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `tag_unique` (`tag`),
  UNIQUE KEY `submission_unique` (`submission_id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `datetime_dosed` (`datetime_dosed`),
  KEY `datetime_run` (`datetime_run`),
  KEY `experimentalist_id` (`experimentalist_id`),
  KEY `plate_id` (`plate_id`),
  KEY `config_file_id` (`config_file_id`),
  KEY `name` (`name`),
  KEY `acclimation_sec` (`acclimation_sec`),
  KEY `incubation_min` (`incubation_min`),
  KEY `sauron_config_id` (`sauron_config_id`),
  KEY `run_to_project` (`experiment_id`),
  CONSTRAINT `run_to_plate` FOREIGN KEY (`plate_id`) REFERENCES `plates` (`id`) ON DELETE CASCADE,
  CONSTRAINT `run_to_project` FOREIGN KEY (`experiment_id`) REFERENCES `experiments` (`id`),
  CONSTRAINT `run_to_sauron_config` FOREIGN KEY (`sauron_config_id`) REFERENCES `sauron_configs` (`id`),
  CONSTRAINT `run_to_submission` FOREIGN KEY (`submission_id`) REFERENCES `submissions` (`id`),
  CONSTRAINT `run_to_sauronx_toml` FOREIGN KEY (`config_file_id`) REFERENCES `config_files` (`id`),
  CONSTRAINT `run_to_user` FOREIGN KEY (`experimentalist_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `sauron_configs`
--

CREATE TABLE `sauron_configs` (
  `id` smallint(5) unsigned not null auto_increment,
  `sauron_id` tinyint(3) unsigned not null,
  `datetime_changed` datetime not null,
  `description` text not null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `sauron_datetime_changed_unique` (`sauron_id`, `datetime_changed`),
  KEY `sauron_id` (`sauron_id`),
  CONSTRAINT `sauron_config_to_sauron` FOREIGN KEY (`sauron_id`) REFERENCES `saurons` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `sauron_settings`
--

CREATE TABLE `sauron_settings` (
  `id` smallint(5) unsigned not null auto_increment,
  `sauron_config_id` smallint(5) unsigned not null,
  `name` varchar(255) not null,
  `value` varchar(255) not null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `sauron_name_unique` (`sauron_config_id`, `name`),
  KEY `name` (`name`),
  KEY `sauron_config_id` (`sauron_config_id`),
  CONSTRAINT `sauron_setting_to_sauron_config` FOREIGN KEY (`sauron_config_id`) REFERENCES `sauron_configs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `saurons`
--

CREATE TABLE `saurons` (
  `id` tinyint(3) unsigned not null auto_increment,
  `name` varchar(50) not null,
  `active` bool not null default 0,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `number` (`name`),
  KEY `current` (`active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `sensor_data`
--

CREATE TABLE `sensor_data` (
  `id` mediumint(8) unsigned not null auto_increment,
  `run_id` mediumint(8) unsigned not null,
  `sensor_id` tinyint(3) unsigned not null,
  `floats` longblob not null,
  `floats_sha1` binary(20) not null,
  PRIMARY KEY (`id`),
  KEY `run_id` (`run_id`),
  KEY `sensor_id` (`sensor_id`),
  KEY `floats_sha1` (`floats_sha1`),
  CONSTRAINT `sensor_data_to_run` FOREIGN KEY (`run_id`) REFERENCES `runs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `sensor_data_to_sensor` FOREIGN KEY (`sensor_id`) REFERENCES `sensors` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `sensors`
--

CREATE TABLE `sensors` (
  `id` tinyint(3) unsigned not null auto_increment,
  `name` varchar(50) not null,
  `description` varchar(250) default null,
  `data_type` enum(
      'byte', 'short', 'int',
      'float', 'double',
      'unsigned_byte', 'unsigned_short', 'unsigned_int', 'unsigned_float', 'unsigned_double',
      'utf8_char',
      'long', 'unsigned_long',
      'other'
  ) not null,
  `blob_type` enum('assay_start', 'battery_start', 'every_n_milliseconds', 'every_n_frames', 'arbitrary') default null,
  `n_between` int(10) unsigned default null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `stimuli`
--

CREATE TABLE `stimuli` (
  `id` smallint(5) unsigned not null auto_increment,
  `name` varchar(50) not null,
  `default_color` char(6) not null,
  `description` varchar(250) default null,
  `analog` bool not null default 0,
  `rgb` binary(3) default null,
  `wavelength_nm` smallint(5) unsigned default null,
  `audio_file_id` smallint(5) unsigned default null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  UNIQUE KEY `audio_file_id_unique` (`audio_file_id`),
  CONSTRAINT `stimulus_to_audio_file` FOREIGN KEY (`audio_file_id`) REFERENCES `audio_files` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `stimulus_frames`
--

CREATE TABLE `stimulus_frames` (
  `id` smallint(5) unsigned not null auto_increment,
  `assay_id` smallint(5) unsigned not null,
  `stimulus_id` smallint(5) unsigned not null,
  `frames` longblob not null,
  `frames_sha1` binary(20) not null,
  PRIMARY KEY (`id`),
  UNIQUE KEY `assay_id_stimulus_id` (`assay_id`, `stimulus_id`),
  KEY `assay_id` (`assay_id`),
  KEY `stimulus_id` (`stimulus_id`),
  KEY `frames_sha1` (`frames_sha1`),
  CONSTRAINT `stimulus_frames_to_assay` FOREIGN KEY (`assay_id`) REFERENCES `assays` (`id`) ON DELETE CASCADE,
  CONSTRAINT `stimulus_frames_to_stimulus` FOREIGN KEY (`stimulus_id`) REFERENCES `stimuli` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `submission_params`
--

CREATE TABLE `submission_params` (
  `id` mediumint(8) unsigned not null auto_increment,
  `submission_id` mediumint(8) unsigned not null,
  `name` varchar(250) not null,
  `param_type` enum('n_fish', 'compound', 'dose', 'variant', 'dpf', 'group') not null,
  `value` varchar(4000) not null,
  PRIMARY KEY (`id`),
  UNIQUE KEY `submission_name_unique` (`submission_id`, `name`),
  CONSTRAINT `sub_param_to_sub` FOREIGN KEY (`submission_id`) REFERENCES `submissions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `submission_records`
--

CREATE TABLE `submission_records` (
  `id` int(10) unsigned not null auto_increment,
  `submission_id` mediumint(8) unsigned not null,
  `status` varchar(100) default null,
  `sauron_id` tinyint(3) unsigned not null,
  `datetime_modified` datetime not null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `record_sauron` (`sauron_id`),
  KEY `record_submission` (`submission_id`),
  CONSTRAINT `record_to_sauron` FOREIGN KEY (`sauron_id`) REFERENCES `saurons` (`id`),
  CONSTRAINT `record_to_submission` FOREIGN KEY (`submission_id`) REFERENCES `submissions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `submissions`
--

CREATE TABLE `submissions` (
  `id` mediumint(8) unsigned not null auto_increment,
  `lookup_hash` char(12) not null,
  `experiment_id` smallint(5) unsigned not null,
  `user_id` smallint(5) unsigned not null,
  `person_plated_id` smallint(5) unsigned not null,
  `continuing_id` mediumint(8) unsigned default null,
  `datetime_plated` datetime not null,
  `datetime_dosed` datetime default null,
  `acclimation_sec` int(10) unsigned default null,
  `description` varchar(250) not null,
  `notes` mediumtext default null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_hash_hex` (`lookup_hash`),
  KEY `experiment_id` (`experiment_id`),
  KEY `user_id` (`user_id`),
  KEY `continuing_id` (`continuing_id`),
  KEY `person_plated_id` (`person_plated_id`),
  CONSTRAINT `matched_submission` FOREIGN KEY (`continuing_id`) REFERENCES `submissions` (`id`),
  CONSTRAINT `submission_to_person_plated` FOREIGN KEY (`person_plated_id`) REFERENCES `users` (`id`),
  CONSTRAINT `submission_to_experiment` FOREIGN KEY (`experiment_id`) REFERENCES `experiments` (`id`),
  CONSTRAINT `submission_to_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `projects`
--

CREATE TABLE `projects` (
  `id` smallint(5) unsigned not null auto_increment,
  `name` varchar(100) not null,
  `type_id` tinyint(3) unsigned default null,
  `creator_id` smallint(5) unsigned not null,
  `description` varchar(10000) default null,
  `reason` mediumtext default null,
  `methods` mediumtext default null,
  `active` bool not null default 1,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `creator_id` (`creator_id`),
  KEY `type_id` (`type_id`),
  CONSTRAINT `project_to_project_type` FOREIGN KEY (`type_id`) REFERENCES `project_types` (`id`),
  CONSTRAINT `project_to_user` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `suppliers`
--

CREATE TABLE `suppliers` (
  `id` smallint(5) unsigned not null auto_increment,
  `name` varchar(50) not null,
  `description` varchar(250) default null,
  `created` datetime not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `template_assays`
--

CREATE TABLE `template_assays` (
  `id` smallint(5) unsigned not null auto_increment,
  `name` varchar(100) not null,
  `description` varchar(10000) default null,
  `author_id` smallint(5) unsigned default null,
  `specializes` smallint(5) unsigned default null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `author_id` (`author_id`),
  KEY `specializes` (`specializes`),
  CONSTRAINT `ta_to_parent` FOREIGN KEY (`specializes`) REFERENCES `template_assays` (`id`) ON DELETE SET NULL,
  CONSTRAINT `ta_to_user` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `template_plates`
--

CREATE TABLE `template_plates` (
  `id` smallint(5) unsigned not null auto_increment,
  `name` varchar(100) not null,
  `description` varchar(10000) default null,
  `plate_type_id` tinyint(3) unsigned not null,
  `author_id` smallint(5) unsigned not null,
  `hidden` bool not null default 0,
  `created` timestamp not null default current_timestamp(),
  `specializes` smallint(5) unsigned default null,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `author_id` (`author_id`),
  KEY `specializes` (`specializes`),
  KEY `plate_type_id` (`plate_type_id`),
  CONSTRAINT `tp_to_parent` FOREIGN KEY (`specializes`) REFERENCES `template_plates` (`id`) ON DELETE SET NULL,
  CONSTRAINT `tp_to_plate_type` FOREIGN KEY (`plate_type_id`) REFERENCES `plate_types` (`id`),
  CONSTRAINT `tp_to_user` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `template_stimulus_frames`
--

CREATE TABLE `template_stimulus_frames` (
  `id` mediumint(6) unsigned not null auto_increment,
  `template_assay_id` smallint(5) unsigned not null,
  `range_expression` varchar(150) not null,
  `stimulus_id` smallint(5) unsigned not null,
  `value_expression` varchar(250) not null,
  PRIMARY KEY (`id`),
  KEY `stimulus_id` (`stimulus_id`),
  KEY `template_assay_id` (`template_assay_id`),
  CONSTRAINT `tsf_to_ta` FOREIGN KEY (`template_assay_id`) REFERENCES `template_assays` (`id`) ON DELETE CASCADE,
  CONSTRAINT `tsf_to_s` FOREIGN KEY (`stimulus_id`) REFERENCES `stimuli` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `template_treatments`
--

CREATE TABLE `template_treatments` (
  `id` mediumint(8) unsigned not null auto_increment,
  `template_plate_id` smallint(5) unsigned not null,
  `well_range_expression` varchar(100) not null,
  `batch_expression` varchar(250) not null,
  `dose_expression` varchar(200) not null,
  PRIMARY KEY (`id`),
  KEY `template_plate_id` (`template_plate_id`),
  CONSTRAINT `tt_to_tp` FOREIGN KEY (`template_plate_id`) REFERENCES `template_plates` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `template_wells`
--

CREATE TABLE `template_wells` (
  `id` mediumint(8) unsigned not null auto_increment,
  `template_plate_id` smallint(5) unsigned not null,
  `well_range_expression` varchar(255) not null,
  `control_type_id` tinyint(3) unsigned default null,
  `n_expression` varchar(250) not null,
  `variant_expression` varchar(250) not null,
  `age_expression` varchar(255) not null,
  `group_expression` varchar(255) not null,
  PRIMARY KEY (`id`),
  KEY `template_plate_id` (`template_plate_id`),
  KEY `control_type_id` (`control_type_id`),
  CONSTRAINT `tw_to_control_type` FOREIGN KEY (`control_type_id`) REFERENCES `control_types` (`id`),
  CONSTRAINT `tw_to_tp` FOREIGN KEY (`template_plate_id`) REFERENCES `template_plates` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `transfer_plates`
--

CREATE TABLE `transfer_plates` (
  `id` smallint(5) unsigned not null auto_increment,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci not null,
  `description` varchar(250) COLLATE utf8mb4_unicode_ci default null,
  `plate_type_id` tinyint(3) unsigned not null,
  `supplier_id` smallint(5) unsigned default null,
  `parent_id` smallint(5) unsigned default null,
  `dilution_factor_from_parent` double unsigned default null,
  `initial_ul_per_well` double unsigned not null,
  `creator_id` smallint(5) unsigned not null,
  `datetime_created` datetime not null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `plate_type_id` (`plate_type_id`),
  KEY `creator_id` (`creator_id`),
  KEY `parent_id` (`parent_id`),
  KEY `supplier_id` (`supplier_id`),
  CONSTRAINT `transfer_plate_to_creator` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`),
  CONSTRAINT `transfer_plate_to_parent` FOREIGN KEY (`parent_id`) REFERENCES `transfer_plates` (`id`),
  CONSTRAINT `transfer_plate_to_plate_type` FOREIGN KEY (`plate_type_id`) REFERENCES `plate_types` (`id`),
  CONSTRAINT `transfer_plate_to_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` smallint(5) unsigned not null auto_increment,
  `username` varchar(20) not null,
  `first_name` varchar(30) not null,
  `last_name` varchar(30) not null,
  `write_access` bool not null default 1,
  `bcrypt_hash` char(60) CHARACTER SET utf8 COLLATE utf8_bin default null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `username_unique` (`username`),
  KEY `bcrypt_hash` (`bcrypt_hash`),
  KEY `first_name` (`first_name`),
  KEY `last_name` (`last_name`),
  KEY `write_access` (`write_access`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `well_features`
--

CREATE TABLE `well_features` (
  `id` mediumint(8) unsigned not null auto_increment,
  `well_id` mediumint(8) unsigned not null,
  `type_id` tinyint(3) unsigned not null,
  `floats` longblob not null,
  `sha1` binary(40) not null,
  PRIMARY KEY (`id`),
  KEY `type_id` (`type_id`),
  KEY `sha1` (`sha1`),
  KEY `well_id` (`well_id`),
  CONSTRAINT `well_feature_to_type` FOREIGN KEY (`type_id`) REFERENCES `features` (`id`),
  CONSTRAINT `well_feature_to_well` FOREIGN KEY (`well_id`) REFERENCES `wells` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `well_treatments`
--

CREATE TABLE `well_treatments` (
  `id` int(10) unsigned not null auto_increment,
  `well_id` mediumint(8) unsigned not null,
  `batch_id` mediumint(8) unsigned not null,
  `micromolar_dose` double unsigned default null,
  PRIMARY KEY (`id`),
  UNIQUE KEY `well_batch_unique` (`well_id`, `batch_id`),
  KEY `batch_id` (`batch_id`),
  KEY `well_id` (`well_id`),
  CONSTRAINT `well_treatment_to_batch` FOREIGN KEY (`batch_id`) REFERENCES `batches` (`id`),
  CONSTRAINT `well_treatment_to_well` FOREIGN KEY (`well_id`) REFERENCES `wells` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `wells`
--

CREATE TABLE `wells` (
  `id` mediumint(8) unsigned not null auto_increment,
  `run_id` mediumint(8) unsigned not null,
  `well_index` smallint(5) unsigned not null,
  `control_type_id` tinyint(3) unsigned default null,
  `variant_id` mediumint(8) unsigned default null,
  `well_group` varchar(50) default null,
  `n` mediumint(9) not null default 0,
  `age` mediumint(8) unsigned default null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `plate_well_index_unique` (`run_id`, `well_index`),
  KEY `run_id` (`run_id`),
  KEY `variant_id` (`variant_id`),
  KEY `well_group` (`well_group`),
  KEY `control_type_id` (`control_type_id`),
  KEY `n` (`n`),
  KEY `well_index` (`well_index`),
  CONSTRAINT `well_to_control_type` FOREIGN KEY (`control_type_id`) REFERENCES `control_types` (`id`),
  CONSTRAINT `well_to_variant` FOREIGN KEY (`variant_id`) REFERENCES `genetic_variants` (`id`),
  CONSTRAINT `well_to_run` FOREIGN KEY (`run_id`) REFERENCES `runs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;



--
-- Table structure for table `mandos_info`
--

CREATE TABLE `mandos_info` (
  `id` mediumint(8) unsigned not null auto_increment,
  `compound_id` mediumint(8) unsigned not null,
  `name` varchar(100) not null,
  `value` varchar(1000) not null,
  `ref_id` smallint(5) unsigned not null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `mandos_chem_info_name_ref_compound_unique` (`name`, `ref_id`, `compound_id`),
  KEY `ref_id` (`ref_id`),
  KEY `name` (`name`),
  KEY `value` (`value`),
  KEY `compound_id` (`compound_id`),
  CONSTRAINT `mandos_chem_info_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `mandos_info_to_compound` FOREIGN KEY (`compound_id`) REFERENCES `compounds` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `mandos_object_links`
--

CREATE TABLE `mandos_object_links` (
  `id` int(10) unsigned not null auto_increment,
  `parent_id` mediumint(8) unsigned not null,
  `child_id` mediumint(8) unsigned not null,
  `ref_id` smallint(5) unsigned not null,
  PRIMARY KEY (`id`),
  KEY `parent_id` (`parent_id`),
  KEY `child_id` (`child_id`),
  KEY `ref_id` (`ref_id`),
  CONSTRAINT `mandos_ol_to_child` FOREIGN KEY (`child_id`) REFERENCES `mandos_objects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mandos_ol_to_parent` FOREIGN KEY (`parent_id`) REFERENCES `mandos_objects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mandos_ol_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


--
-- Table structure for table `mandos_object_tags`
--

CREATE TABLE `mandos_object_tags` (
  `id` int(10) unsigned not null auto_increment,
  `object` mediumint(8) unsigned not null,
  `ref` smallint(5) unsigned not null,
  `name` varchar(150) not null,
  `value` varchar(250) not null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `object_ref_name_value_unique` (`object`, `ref`, `name`, `value`),
  KEY `object` (`object`),
  KEY `ref` (`ref`),
  KEY `label` (`value`),
  CONSTRAINT `mot_to_object` FOREIGN KEY (`object`) REFERENCES `mandos_objects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mot_to_ref` FOREIGN KEY (`ref`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `mandos_objects`
--

CREATE TABLE `mandos_objects` (
  `id` mediumint(8) unsigned not null auto_increment,
  `ref_id` smallint(5) unsigned not null,
  `external_id` varchar(250) not null,
  `name` varchar(250) default null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `ref_external_id_unique` (`ref_id`, `external_id`),
  KEY `ref_id` (`ref_id`),
  KEY `external_id` (`external_id`),
  CONSTRAINT `mo_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `mandos_predicates`
--

CREATE TABLE `mandos_predicates` (
  `id` tinyint(3) unsigned not null auto_increment,
  `ref_id` smallint(5) unsigned not null,
  `external_id` varchar(250) default null,
  `name` varchar(250) not null,
  `kind` enum('target', 'class', 'indication', 'other') not null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_ref_unique` (`name`, `ref_id`),
  UNIQUE KEY `external_id_ref_unique` (`external_id`, `ref_id`),
  KEY `ref_id` (`ref_id`),
  KEY `name` (`name`),
  KEY `external_id` (`external_id`),
  CONSTRAINT `mp_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `mandos_rule_tags`
--

CREATE TABLE `mandos_rule_tags` (
  `id` int(10) unsigned not null auto_increment,
  `rule` int(10) unsigned not null,
  `ref` smallint(5) unsigned not null,
  `name` varchar(150) not null,
  `value` varchar(250) not null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `rule_ref_name_value_unique` (`rule`, `ref`, `name`, `value`),
  KEY `rule` (`rule`),
  KEY `label` (`value`),
  KEY `ref` (`ref`),
  CONSTRAINT `mandos_rule_tag_to_object` FOREIGN KEY (`rule`) REFERENCES `mandos_rules` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mandos_rule_tag_to_ref` FOREIGN KEY (`ref`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `mandos_rules`
--

CREATE TABLE `mandos_rules` (
  `id` int(10) unsigned not null auto_increment,
  `ref_id` smallint(5) unsigned not null,
  `compound_id` mediumint(8) unsigned not null,
  `object_id` mediumint(8) unsigned not null,
  `external_id` varchar(250) default null,
  `predicate_id` tinyint(3) unsigned not null,
  `created` timestamp not null default current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `ref_compound_mode_unique` (`ref_id`, `compound_id`, `object_id`, `predicate_id`),
  KEY `ref_id` (`ref_id`),
  KEY `compound_id` (`compound_id`),
  KEY `external_id` (`external_id`),
  KEY `object_id` (`object_id`),
  KEY `predicate_id` (`predicate_id`),
  CONSTRAINT `mr_to_cmpd` FOREIGN KEY (`compound_id`) REFERENCES `compounds` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mr_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mr_to_mo` FOREIGN KEY (`object_id`) REFERENCES `mandos_objects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mo_to_pred` FOREIGN KEY (`predicate_id`) REFERENCES `mandos_predicates` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


INSERT INTO refs(
    id, name, datetime_downloaded, external_version, description, url
) VALUES (
    4, 'ref_four', '2019-01-29 12:48:12', 'ref_four_external_version', 'this is ref four',
    'https://www.nonexistentreffour.com'
);
