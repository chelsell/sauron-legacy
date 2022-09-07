
-- MariaDB 10.17
-- Database: valar
/*!40101 SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci */;

CREATE DATABASE valar CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
USE valar;


--
-- Table structure for table `annotations`
--

CREATE TABLE `annotations` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL COMMENT 'A short optional key. This is meant to be used to filter data for analyses. For example, excluding runs annotated for "count:missing-frames" with value > 2.',
  `value` varchar(255) DEFAULT NULL COMMENT 'An optional value, such as a number of missing frames or computed image fuzziness.',
  `level` enum('0:good','1:note','2:caution','3:warning','4:danger','9:deleted','to_fix','fixed') NOT NULL DEFAULT '1:note',
  `run_id` mediumint(8) unsigned DEFAULT NULL,
  `submission_id` mediumint(8) unsigned DEFAULT NULL COMMENT 'This is important for adding annotations before the data has been inserted.',
  `well_id` mediumint(8) unsigned DEFAULT NULL COMMENT 'If set, indicates that this annotation applies to only this well. Just make duplicate records if multiple wells are affected.',
  `assay_id` smallint(5) unsigned DEFAULT NULL COMMENT 'If set, indicates that this annotation applies to only one assay. Just make duplicate records if needed.',
  `annotator_id` smallint(5) unsigned NOT NULL,
  `description` mediumtext DEFAULT NULL COMMENT 'An optional description. For example, "one of the 4 red LEDs had burned out."',
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `annotation_to_run` (`run_id`),
  KEY `annotation_to_well` (`well_id`),
  KEY `annotation_to_assay` (`assay_id`),
  KEY `annotation_to_person` (`annotator_id`),
  KEY `level` (`level`),
  KEY `name` (`name`),
  KEY `annotation_to_submission` (`submission_id`),
  KEY `value` (`value`),
  CONSTRAINT `annotation_to_run` FOREIGN KEY (`run_id`) REFERENCES `runs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `annotation_to_assay` FOREIGN KEY (`assay_id`) REFERENCES `assays` (`id`) ON DELETE CASCADE,
  CONSTRAINT `annotation_to_user` FOREIGN KEY (`annotator_id`) REFERENCES `users` (`id`),
  CONSTRAINT `annotation_to_submission` FOREIGN KEY (`submission_id`) REFERENCES `submissions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `annotation_to_well` FOREIGN KEY (`well_id`) REFERENCES `wells` (`id`) ON DELETE CASCADE
) COMMENT='
    User-created and automated text strings about runs.
    Each may specify single wells and/or assays.
    Examples include flags about invalid data, and membership in data sets.
';

--
-- Table structure for table `assay_params`
--
CREATE TABLE `assay_params` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `assay_id` smallint(5) unsigned NOT NULL,
  `name` varchar(30) NOT NULL COMMENT 'This should begin with a dollar sign ($).',
  `value` double NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_assay_unique` (`name`,`assay_id`),
  KEY `assay_param_to_assay` (`assay_id`),
  KEY `value` (`value`),
  CONSTRAINT `assay_param_to_assay` FOREIGN KEY (`assay_id`) REFERENCES `assays` (`id`) ON DELETE CASCADE
) COMMENT='
    Rarely-used table that specifies parameter choices in parameterized template assays.
';

--
-- Table structure for table `assay_positions`
--

CREATE TABLE `assay_positions` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `battery_id` smallint(5) unsigned NOT NULL,
  `assay_id` smallint(5) unsigned NOT NULL,
  `start` int(10) unsigned NOT NULL COMMENT 'The number of milliseconds into the battery that this assay starts.',
  PRIMARY KEY (`id`),
  UNIQUE KEY `battery_assay_start_unique` (`battery_id`,`assay_id`,`start`),
  KEY `battery_id` (`battery_id`),
  KEY `assay_id` (`assay_id`),
  KEY `start` (`start`),
  CONSTRAINT `assay_position_to_assay` FOREIGN KEY (`assay_id`) REFERENCES `assays` (`id`),
  CONSTRAINT `assay_position_to_battery` FOREIGN KEY (`battery_id`) REFERENCES `batteries` (`id`) ON DELETE CASCADE
) COMMENT='
    Specifies which assays are in a battery.
    Note that each assay must start exactly at the end of the previous.
    The millisecond times are defined inclusive-exclusive, so start for the (n+1)-th assay
    must equal (start + length) for the n-th assay.
';

--
-- Table structure for table `assays`
--

CREATE TABLE `assays` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(250) NOT NULL,
  `description` varchar(5000) DEFAULT NULL,
  `length` int(10) unsigned NOT NULL,
  `hidden` tinyint(1) NOT NULL DEFAULT 0 COMMENT 'Set to 1 to hide on the website. This value can change at any time.',
  `template_assay_id` smallint(5) unsigned DEFAULT NULL,
  `frames_sha1` binary(20) NOT NULL COMMENT 'An SHA-1 hash that uniquely identifies the frames data. Computed from stimulus_frames.hashes and the length. See the docs. ',
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `frames_sha1_unique` (`frames_sha1`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `name` (`name`),
  KEY `frames_sha1` (`frames_sha1`) USING BTREE,
  KEY `assay_to_template_assay` (`template_assay_id`),
  CONSTRAINT `assay_to_template_assay` FOREIGN KEY (`template_assay_id`) REFERENCES `template_assays` (`id`)
) COMMENT='
    A concrete assay containing one or more stimulus time-series.
';

--
-- Table structure for table `audio_files`
--

CREATE TABLE `audio_files` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `filename` varchar(100) NOT NULL COMMENT 'The corresponding stimulus name is almost exclusively used instead.',
  `notes` varchar(250) DEFAULT NULL,
  `n_seconds` double unsigned NOT NULL COMMENT 'This is important. Do not round; use the full precision of a double.',
  `data` mediumblob NOT NULL COMMENT 'Should generally be WAV data.',
  `sha1` binary(20) NOT NULL COMMENT 'An SHA-1 hash of the file contents.',
  `creator_id` smallint(5) unsigned DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `filename_unique` (`filename`),
  UNIQUE KEY `sha1_unique` (`sha1`),
  KEY `creator_id` (`creator_id`),
  CONSTRAINT `audio_file_to_user` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) COMMENT='
    Stored audio files corresponding to stimuli. In general, these will be WAV.
';

--
-- Table structure for table `batch_annotations`
--

CREATE TABLE `batch_annotations` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `batch_id` mediumint(8) unsigned NOT NULL,
  `level` enum('0:good','1:note','2:caution','3:warning','4:danger','9:deleted') NOT NULL DEFAULT '1:note',
  `name` varchar(50) DEFAULT NULL,
  `value` varchar(200) DEFAULT NULL COMMENT 'An optional value, rarely needed.',
  `description` varchar(200) DEFAULT NULL,
  `annotator_id` smallint(5) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `batch_id` (`batch_id`),
  KEY `annotator_id` (`annotator_id`),
  KEY `level` (`level`),
  KEY `name` (`name`),
  KEY `value` (`value`),
  CONSTRAINT `batch_annotation_to_batch` FOREIGN KEY (`batch_id`) REFERENCES `batches` (`id`) ON DELETE CASCADE,
  CONSTRAINT `batch_annotation_to_user` FOREIGN KEY (`annotator_id`) REFERENCES `users` (`id`)
) COMMENT='
    Flexible annotations and concerns about compound batches, typically user-supplied.
';

--
-- Table structure for table `batch_labels`
--

CREATE TABLE `batch_labels` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `batch_id` mediumint(8) unsigned NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `name` varchar(250) NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `name` (`name`),
  KEY `ref_id` (`ref_id`),
  KEY `batch_id` (`batch_id`),
  CONSTRAINT `batch_label_to_batch` FOREIGN KEY (`batch_id`) REFERENCES `batches` (`id`) ON DELETE CASCADE,
  CONSTRAINT `batch_label_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) COMMENT='
    Typically, internal IDs for individual batches.
    For example, an ID from the supplier, or a compound name used by a collaborator.
    Names for the compounds themselves should instead be listed in compound_labels.
';

--
-- Table structure for table `batches`
--

CREATE TABLE `batches` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `lookup_hash` varchar(14) NOT NULL COMMENT 'An auto-generated string ID. These should prevent getting a valid ID if mistyped.',
  `tag` varchar(100) DEFAULT NULL COMMENT 'Rarely used. An exact label that should be preferred over any entry in batch_labels',
  `compound_id` mediumint(8) unsigned DEFAULT NULL,
  `made_from_id` mediumint(8) unsigned DEFAULT NULL COMMENT 'Point to the batch this was diluted or transferred from, if any.',
  `supplier_id` smallint(5) unsigned DEFAULT NULL COMMENT 'A store or lab that the batch came from.',
  `ref_id` smallint(5) unsigned DEFAULT NULL COMMENT 'This may point to a specific library or way that the data was entered.',
  `legacy_internal_id` varchar(255) DEFAULT NULL COMMENT 'If needed to handle IDs or barcodes from a legacy system. These can be displayed more prominently than entries in batch_labels.',
  `location_id` smallint(5) unsigned DEFAULT NULL COMMENT 'Something like a freezer, shelf, or room number. Displayed to help locate the compound.',
  `box_number` smallint(5) unsigned DEFAULT NULL COMMENT 'A numerical box ID marking where the batch is stored, if relevant.',
  `well_number` smallint(5) unsigned DEFAULT NULL COMMENT 'A specific well number if the batch is stored in a box.',
  `location_note` varchar(20) DEFAULT NULL COMMENT 'A flexible comment to help find the compound.',
  `amount` varchar(100) DEFAULT NULL COMMENT 'A volume or mass of the batch when it was created, if known and needed. This is especially important for dry powders and when amounts need to be tracked for legal reasons. Add the units after the value.',
  `concentration_millimolar` double unsigned DEFAULT NULL COMMENT 'The concentration of the compound, if in solution.',
  `solvent_id` mediumint(8) unsigned DEFAULT NULL COMMENT 'An ID in the compounds table if in solution.',
  `molecular_weight` double unsigned DEFAULT NULL,
  `supplier_catalog_number` varchar(20) DEFAULT NULL,
  `person_ordered` smallint(5) unsigned DEFAULT NULL,
  `date_ordered` date DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `suspicious` tinyint(1) NOT NULL DEFAULT 0 COMMENT 'Legacy flag for something potentially wrong with the metadata listed in this row.',
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_hash` (`lookup_hash`),
  UNIQUE KEY `box_number_well_number` (`box_number`,`well_number`),
  UNIQUE KEY `tag_unique` (`tag`),
  KEY `compound_id` (`compound_id`),
  KEY `solvent_id` (`solvent_id`),
  KEY `legacy_internal_id` (`legacy_internal_id`),
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
) COMMENT='
    A batch of a compound.
    Each new receipt (e.g. purchase) of a compound should be given a new
    Names for the compounds themselves should instead be listed in compound_labels.
';

--
-- Table structure for table `batteries`
--

CREATE TABLE `batteries` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` varchar(10000) DEFAULT NULL,
  `length` int(10) unsigned NOT NULL,
  `author_id` smallint(5) unsigned DEFAULT NULL,
  `template_id` smallint(5) unsigned DEFAULT NULL,
  `hidden` tinyint(1) NOT NULL DEFAULT 0 COMMENT 'Whether to hide the battery in the website. This can be modified at any time.',
  `notes` varchar(10000) DEFAULT NULL,
  `assays_sha1` binary(20) NOT NULL COMMENT 'A hash of all of the data (including stimulus frames). This has a specific technical definition; see the docs.',
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `creator_id` (`author_id`),
  KEY `battery_to_template` (`template_id`),
  KEY `length` (`length`),
  KEY `assays_sha1` (`assays_sha1`),
  CONSTRAINT `battery_to_user` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`)
) COMMENT='
    A series of assays in order.
';

--
-- Table structure for table `compound_labels`
--

CREATE TABLE `compound_labels` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `compound_id` mediumint(8) unsigned NOT NULL,
  `name` varchar(1000) NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `compound_id` (`compound_id`),
  KEY `compound_label_to_ref` (`ref_id`),
  CONSTRAINT `compound_label_to_compound` FOREIGN KEY (`compound_id`) REFERENCES `compounds` (`id`) ON DELETE CASCADE,
  CONSTRAINT `compound_label_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) COMMENT='
    A name or ID for the compound. This could be an external database ID, SMILES, IUPAC name, etc.
    Names for individual batches should instead be listed in batch_labels.
';

--
-- Table structure for table `compounds`
--

CREATE TABLE `compounds` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `inchi` varchar(2000) NULL COMMENT 'Only use STANDARD InChI, and include the InChI= prefix. Include exactly the stereochemistry that is specified by the supplier; leave stereocenters unassigned as needed.',
  `inchikey` char(27) NULL COMMENT 'The standard InChI Key. All should be standard and correspondingly end with -S.',
  `inchikey_connectivity` char(14) AS (substring(inchikey, 14)) COMMENT 'The substring of the InChI Key that only includes the connectivity of atoms. Useful to quickly find all stereoisomers of a compound.',
  `chembl_id` varchar(20) DEFAULT NULL COMMENT 'The corresponding ChEMBL compound ID, including the "CHEMBL" prefix. This should correspond to the exact InChI. If you need to link to a better-annotated (e.g. sanitized) compound, add that to compound_labels.',
  `chemspider_id` int(10) unsigned DEFAULT NULL COMMENT 'May be used for linking to SVGs or purchasing information. Do not change this value after creation.',
  `smiles` varchar(2000) DEFAULT NULL COMMENT 'An SMILES string that EXACTLY matches the InChI Key. Using a standard form under a chosen canonicalization algorithm is recommended.',
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `inchikey` (`inchikey`),
  KEY `inchikey_connectivity` (`inchikey_connectivity`),
  KEY `chembl_id` (`chembl_id`),
  KEY `chemspider_id` (`chemspider_id`)
) COMMENT='
    A distinct chemical entity.
    These should almost always be compounds, salts, etc.
    If required, you can leave the InChI, SMILES, and InChI Key as null for mixtures, etc.
';

--
-- Table structure for table `config_files`
--

CREATE TABLE `config_files` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `toml_text` mediumtext NOT NULL,
  `text_sha1` binary(20) NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `text_sha1_unique` (`text_sha1`),
  KEY `text_sha1` (`text_sha1`)
) COMMENT='
    A TOML config file from SauronX.
    This is sometimes needed to extract metadata in analyses.
';

--
-- Table structure for table `control_types`
--

CREATE TABLE `control_types` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` varchar(250) NOT NULL,
  `positive` tinyint(1) NOT NULL COMMENT 'Sometimes ambiguous but used by sauronlab.',
  `drug_related` tinyint(1) NOT NULL DEFAULT 1,
  `genetics_related` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `name` (`name`),
  KEY `positive` (`positive`),
  KEY `drug_related` (`drug_related`),
  KEY `genetics_related` (`genetics_related`)
) COMMENT='
    A type of control, such as "solvent".
    Control types are marked as negative or positive, although those terms are sometimes ambiguous.
    A handful mark critical information other than control type. For example, marking wells that should not be used.
';

--
-- Table structure for table `experiment_tags`
--

CREATE TABLE `experiment_tags` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `experiment_id` smallint(5) unsigned NOT NULL,
  `name` varchar(100) NOT NULL,
  `value` varchar(255) NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `experiment_name_unique` (`experiment_id`,`name`),
  KEY `ref_id` (`ref_id`),
  CONSTRAINT `experiment_tag_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `tag_to_experiment` FOREIGN KEY (`experiment_id`) REFERENCES `experiments` (`id`) ON DELETE CASCADE
) COMMENT='
    Flexible string metadata about experiments, typically user-supplied.
';

--
-- Table structure for table `experiments`
--

CREATE TABLE `experiments` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `description` varchar(10000) DEFAULT NULL,
  `creator_id` smallint(5) unsigned NOT NULL,
  `project_id` smallint(5) unsigned NOT NULL,
  `battery_id` smallint(5) unsigned NOT NULL,
  `template_plate_id` smallint(5) unsigned DEFAULT NULL,
  `transfer_plate_id` smallint(5) unsigned DEFAULT NULL,
  `default_acclimation_sec` smallint(5) unsigned NOT NULL COMMENT 'When creating a new submission, use this number of seconds for dark acclimation unless the user overrides it.',
  `notes` text DEFAULT NULL COMMENT 'Whether to show the experiment on the website. Can change at any time.',
  `active` tinyint(1) NOT NULL DEFAULT 1,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `battery_id` (`battery_id`),
  KEY `project_id` (`project_id`),
  KEY `template_plate_id` (`template_plate_id`),
  KEY `transfer_plate_id` (`transfer_plate_id`) COMMENT 'Marks a mother plate for transfer.',
  KEY `creator_id` (`creator_id`),
  CONSTRAINT `experiment_to_transfer_plate` FOREIGN KEY (`transfer_plate_id`) REFERENCES `transfer_plates` (`id`),
  CONSTRAINT `experiment_to_user` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`),
  CONSTRAINT `project_to_battery` FOREIGN KEY (`battery_id`) REFERENCES `batteries` (`id`),
  CONSTRAINT `experiment_to_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `project_to_template_plate` FOREIGN KEY (`template_plate_id`) REFERENCES `template_plates` (`id`)
) COMMENT='
    A set of data collected for the same purpose and that can be analyzed together.
    Runs of the same project must have the same battery and overall plate layout.
';

--
-- Table structure for table `features`
--

CREATE TABLE `features` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` varchar(250) NOT NULL,
  `dimensions` varchar(20) NOT NULL COMMENT 'Indicates the dimensionality of the data in the form "[d1,d2,...d3]". Each element should be either T for the number of frames or an integer.',
  `data_type` enum('byte','short','int','float','double','unsigned_byte','unsigned_short','unsigned_int','unsigned_float','unsigned_double','utf8_char') NOT NULL DEFAULT 'float',
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`)
) COMMENT='
    Something that can be calculated on video data.
';

--
-- Table structure for table `gene_labels`
--

CREATE TABLE `gene_labels` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `gene_id` mediumint(8) unsigned NOT NULL,
  `name` varchar(255) NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `gene_name_ref_unique` (`gene_id`,`name`,`ref_id`),
  KEY `gene` (`gene_id`),
  KEY `name` (`name`),
  KEY `ref` (`ref_id`),
  CONSTRAINT `gene_label_to_gene` FOREIGN KEY (`gene_id`) REFERENCES `genes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `gene_label_to_source` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) COMMENT='
    A name or ID for a gene.
';

--
-- Table structure for table `genes`
--

CREATE TABLE `genes` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(30) DEFAULT NULL,
  `pub_link` varchar(255) DEFAULT NULL COMMENT 'A hyperlink to a publication, rarely needed.',
  `description` varchar(250) DEFAULT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `user_id` smallint(5) unsigned NOT NULL,
  `raw_file` blob DEFAULT NULL COMMENT 'A file containing the full genetic information, such as a FASTA or .ape file.',
  `raw_file_sha1` binary(20) DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `name` (`name`),
  KEY `pub_link` (`pub_link`),
  KEY `ref_id` (`ref_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `gene_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `gene_to_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) COMMENT='
    A genetic sequence, potentially including specific alleles.
';

--
-- Table structure for table `genetic_construct_features`
--

CREATE TABLE `genetic_construct_features` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `kind` varchar(50) NOT NULL COMMENT 'What kind of feature, e.g. a coding start.',
  `name` varchar(250) NOT NULL,
  `gene_id` mediumint(8) unsigned DEFAULT NULL,
  `construct_id` smallint(5) unsigned NOT NULL,
  `start` bigint(20) DEFAULT NULL,
  `end` bigint(20) DEFAULT NULL,
  `is_complement` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `gene_construct_unique` (`gene_id`,`construct_id`),
  KEY `construct_id` (`construct_id`),
  CONSTRAINT `construct_feature_to_construct` FOREIGN KEY (`construct_id`) REFERENCES `genetic_constructs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `construct_feature_to_gene` FOREIGN KEY (`gene_id`) REFERENCES `genes` (`id`)
) COMMENT='
    Sequence annotations for a genetic construct.
';

--
-- Table structure for table `genetic_constructs`
--

CREATE TABLE `genetic_constructs` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `kind` VARCHAR(100) NOT NULL COMMENT 'A standard string, such as "plasmid" or "guide".',
  `name` varchar(100) NOT NULL,
  `location_id` smallint(5) unsigned DEFAULT NULL,
  `box_number` smallint(5) unsigned NOT NULL,
  `tube_number` smallint(5) unsigned NOT NULL,
  `description` varchar(250) NOT NULL,
  `supplier_id` smallint(5) unsigned DEFAULT NULL,
  `ref_id` smallint(5) unsigned NOT NULL COMMENT 'Where this metadata came from. Typically, this will be the website or another tool.',
  `pmid` varchar(30) DEFAULT NULL COMMENT 'A PubMed ID where the construct is described.',
  `pub_link` varchar(150) DEFAULT NULL COMMENT 'A hyperlink where the construct is described.',
  `creator_id` smallint(5) unsigned NOT NULL,
  `date_made` datetime DEFAULT NULL,
  `selection_marker` varchar(50) DEFAULT NULL COMMENT 'The name of a selection marker to use, if applicable.',
  `bacterial_strain` varchar(50) DEFAULT NULL COMMENT 'The name of a bacterial strain used, if applicable.',
  `vector` varchar(50) DEFAULT NULL COMMENT 'The name of the vector, if applicable.',
  `raw_file` blob DEFAULT NULL COMMENT 'A file containing the full genetic information. For example, a .ape file.',
  `raw_file_sha1` binary(20) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `box_tube_unique` (`box_number`,`tube_number`),
  UNIQUE KEY `name_unique` (`name`),
  UNIQUE KEY `raw_file_sha1_unique` (`raw_file_sha1`),
  KEY `creator_id` (`creator_id`),
  KEY `location_id` (`location_id`),
  KEY `box_number` (`box_number`),
  KEY `tube_number` (`tube_number`),
  KEY `bacterial_strain` (`bacterial_strain`),
  KEY `raw_file_sha1` (`raw_file_sha1`),
  KEY `date_made` (`date_made`),
  KEY `kind` (`kind`),
  KEY `vector` (`vector`),
  KEY `pmid` (`pmid`),
  KEY `supplier_id` (`supplier_id`),
  KEY `ref_id` (`ref_id`),
  CONSTRAINT `construct_to_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`),
  CONSTRAINT `genetic_construct_to_location` FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`),
  CONSTRAINT `genetic_construct_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `plasmid_to_user` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) COMMENT='
    A plasmid, crispr guide, or any other kind of genetic sequence that is used for modifying the germline or expression.
';

--
-- Table structure for table `genetic_variants`
--

CREATE TABLE `genetic_variants` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(250) NOT NULL,
  `mother_id` mediumint(8) unsigned DEFAULT NULL,
  `father_id` mediumint(8) unsigned DEFAULT NULL,
  `lineage_type` enum('injection','cross','selection','wild-type') DEFAULT NULL COMMENT 'How the variant was derived from previous generations. If "selection", the mother and father refer to the same generation.',
  `date_created` date DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `creator_id` smallint(5) unsigned NOT NULL,
  `fully_annotated` tinyint(1) NOT NULL DEFAULT 1 COMMENT 'Set to 0 if some metadata is missing.',
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `mother_id` (`mother_id`),
  KEY `father_id` (`father_id`),
  KEY `creator_id` (`creator_id`),
  KEY `lineage_type` (`lineage_type`),
  CONSTRAINT `genetic_variant_to_father` FOREIGN KEY (`father_id`) REFERENCES `genetic_variants` (`id`),
  CONSTRAINT `genetic_variant_to_mother` FOREIGN KEY (`mother_id`) REFERENCES `genetic_variants` (`id`),
  CONSTRAINT `genetic_variant_to_user` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) COMMENT='
    A genetic mutation, variant, or set of fish.
';

--
-- Table structure for table `locations`
--

CREATE TABLE `locations` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` varchar(250) NOT NULL DEFAULT '',
  `purpose` varchar(250) NOT NULL DEFAULT '',
  `part_of` smallint(5) unsigned DEFAULT NULL,
  `active` tinyint(1) NOT NULL DEFAULT 1 COMMENT 'Set to 0 to hide in the website. Can change at any time.',
  `temporary` tinyint(1) NOT NULL DEFAULT 0,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `part_of` (`part_of`),
  CONSTRAINT `location_to_location` FOREIGN KEY (`part_of`) REFERENCES `locations` (`id`) ON DELETE SET NULL
) COMMENT='
    A location such as a freezer or room.
';

--
-- Table structure for table `plate_types`
--

CREATE TABLE `plate_types` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `supplier_id` smallint(5) unsigned DEFAULT NULL,
  `part_number` varchar(100) DEFAULT NULL,
  `n_rows` smallint(5) unsigned NOT NULL,
  `n_columns` smallint(5) unsigned NOT NULL,
  `well_shape` enum('round','square','rectangular') NOT NULL,
  `opacity` enum('opaque','transparent') NOT NULL,
  PRIMARY KEY (`id`),
  KEY `n_rows` (`n_rows`,`n_columns`),
  KEY `manufacturer` (`part_number`),
  KEY `supplier_id` (`supplier_id`),
  CONSTRAINT `plate_type_to_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`)
) COMMENT='
    Specifies the number of rows and columns of a plate.
    SauronX stores a distinct ROI configuration per plate_type.
';

--
-- Table structure for table `plates`
--

CREATE TABLE `plates` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `plate_type_id` tinyint(3) unsigned DEFAULT NULL,
  `person_plated_id` smallint(5) unsigned NOT NULL,
  `datetime_plated` datetime DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `datetime_plated` (`datetime_plated`),
  KEY `plate_type_id` (`plate_type_id`),
  KEY `person_plated_id` (`person_plated_id`),
  CONSTRAINT `plate_to_plate_type` FOREIGN KEY (`plate_type_id`) REFERENCES `plate_types` (`id`),
  CONSTRAINT `plate_to_user` FOREIGN KEY (`person_plated_id`) REFERENCES `users` (`id`)
) COMMENT='
    A plate of fish, which can be run multiple times.
';

--
-- Table structure for table `project_tags`
--

CREATE TABLE `project_tags` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `project_id` smallint(5) unsigned NOT NULL,
  `name` varchar(100) NOT NULL,
  `value` varchar(255) NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `project_name_ref_unique` (`project_id`,`name`,`ref_id`),
  KEY `ref_id` (`ref_id`),
  CONSTRAINT `project_tag_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `project_tag_to_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE
) COMMENT='
    Flexible string annotations for projects, typically user-supplied.
';

--
-- Table structure for table `project_types`
--

CREATE TABLE `project_types` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` text NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`)
) COMMENT='
    A very general purpose for a project, such as "reference" or "screening".
';

--
-- Table structure for table `refs`
--

CREATE TABLE `refs` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `datetime_downloaded` datetime DEFAULT NULL,
  `external_version` varchar(50) DEFAULT NULL,
  `description` varchar(250) DEFAULT NULL,
  `url` varchar(100) DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `url` (`url`),
  KEY `name` (`name`),
  KEY `external_version` (`external_version`)
) COMMENT='
    Where data is from. This may be a resource like ChEMBL, a person, publication, or chemical library.
';

--
-- Table structure for table `rois`
--

CREATE TABLE `rois` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `well_id` mediumint(8) unsigned NOT NULL,
  `y0` smallint(6) NOT NULL,
  `x0` smallint(6) NOT NULL,
  `y1` smallint(6) NOT NULL,
  `x1` smallint(6) NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL COMMENT 'Used to distinguish different definitions. For example, "manual" set and an algorithmically computed set.',
  PRIMARY KEY (`id`),
  KEY `well_id` (`well_id`),
  KEY `ref_id` (`ref_id`),
  CONSTRAINT `roi_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `roi_to_well` FOREIGN KEY (`well_id`) REFERENCES `wells` (`id`) ON DELETE CASCADE
) COMMENT='
    Stores the boundaries of individual wells on plates.
';

--
-- Table structure for table `run_tags`
--

CREATE TABLE `run_tags` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `run_id` mediumint(8) unsigned NOT NULL,
  `name` varchar(100) NOT NULL,
  `value` varchar(10000) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `run_name_unique` (`run_id`,`name`),
  CONSTRAINT `run_tag_to_run` FOREIGN KEY (`run_id`) REFERENCES `runs` (`id`) ON DELETE CASCADE
) COMMENT='
    Stores metadata from SauronX itself, such as the date and time completed.
    The names of these are not flexible; specific rows may be needed for insertion and analysis.
    Note that there is also a "tag" column in the runs table.
    Also see the "annotations" table for flexible metadata.
';

--
-- Table structure for table `runs`
--

CREATE TABLE `runs` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `experiment_id` smallint(5) unsigned NOT NULL,
  `plate_id` smallint(5) unsigned NOT NULL,
  `description` varchar(200) NOT NULL,
  `experimentalist_id` smallint(5) unsigned NOT NULL COMMENT 'The person who ran (and typically dosed) the plate.',
  `submission_id` mediumint(8) unsigned DEFAULT NULL,
  `datetime_run` datetime NOT NULL,
  `datetime_dosed` datetime DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL COMMENT 'An auto-generated label for the run that includes information like the username.',
  `tag` varchar(100) NOT NULL DEFAULT '' COMMENT 'An important string that uniquely and immutably marks the data in the form date.time.sauron (e.g. 20210411.142203.Smaug)',
  `sauron_config_id` smallint(5) unsigned NOT NULL,
  `config_file_id` smallint(5) unsigned DEFAULT NULL,
  `incubation_min` mediumint(9) DEFAULT NULL COMMENT 'Can be computed.',
  `acclimation_sec` int(10) unsigned DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `tag_unique` (`tag`),
  UNIQUE KEY `submission_unique` (`submission_id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `datetime_dosed` (`datetime_dosed`),
  KEY `datetime_run` (`datetime_run`),
  KEY `experimentalist_id` (`experimentalist_id`),
  KEY `plate_id` (`plate_id`),
  KEY `submission_id` (`submission_id`),
  KEY `config_file_id` (`config_file_id`),
  KEY `submission_id` (`submission_id`),
  KEY `name` (`name`),
  KEY `acclimation_sec` (`acclimation_sec`),
  KEY `incubation_min` (`incubation_min`),
  KEY `config_file_id` (`config_file_id`),
  KEY `sauron_config_id` (`sauron_config_id`),
  KEY `experiment_id` (`experiment_id`),
  CONSTRAINT `run_to_plate` FOREIGN KEY (`plate_id`) REFERENCES `plates` (`id`) ON DELETE CASCADE,
  CONSTRAINT `run_to_project` FOREIGN KEY (`experiment_id`) REFERENCES `experiments` (`id`),
  CONSTRAINT `run_to_sauron_config` FOREIGN KEY (`sauron_config_id`) REFERENCES `sauron_configs` (`id`),
  CONSTRAINT `run_to_submission` FOREIGN KEY (`submission_id`) REFERENCES `submissions` (`id`),
  CONSTRAINT `run_to_config_file` FOREIGN KEY (`config_file_id`) REFERENCES `config_files` (`id`),
  CONSTRAINT `run_to_user` FOREIGN KEY (`experimentalist_id`) REFERENCES `users` (`id`)
) COMMENT='
    Data that has been fully inserted after SauronX completes.
';

--
-- Table structure for table `sauron_configs`
--

CREATE TABLE `sauron_configs` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `sauron_id` tinyint(3) unsigned NOT NULL,
  `datetime_changed` datetime NOT NULL,
  `description` text NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `sauron_datetime_changed_unique` (`sauron_id`,`datetime_changed`),
  KEY `sauron_id` (`sauron_id`),
  CONSTRAINT `sauron_config_to_sauron` FOREIGN KEY (`sauron_id`) REFERENCES `saurons` (`id`)
) COMMENT='
    The state a Sauron was in for a particular period.
    A new row should be added if something significant changes, such as re-focusing of the camera.
';

--
-- Table structure for table `sauron_settings`
--

CREATE TABLE `sauron_settings` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `sauron_config_id` smallint(5) unsigned NOT NULL,
  `name` varchar(255) NOT NULL,
  `value` varchar(255) NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `sauron_config_name_unique` (`sauron_config_id`,`name`),
  KEY `sauron_setting_name` (`name`),
  KEY `sauron` (`sauron_config_id`),
  CONSTRAINT `sauron_setting_to_sauron_config` FOREIGN KEY (`sauron_config_id`) REFERENCES `sauron_configs` (`id`)
) COMMENT='
    Specifies camera settings such as exposure used for a sauron_config.
';

--
-- Table structure for table `saurons`
--

CREATE TABLE `saurons` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `active` tinyint(1) unsigned NOT NULL DEFAULT 0,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `number` (`name`),
  KEY `current` (`active`)
) COMMENT='
    A single instrument.
';

--
-- Table structure for table `sensor_data`
--

CREATE TABLE `sensor_data` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `run_id` mediumint(8) unsigned NOT NULL,
  `sensor_id` tinyint(3) unsigned NOT NULL,
  `floats` longblob NOT NULL COMMENT 'Mis-named. This is a blob that may contain any type of data.',
  `floats_sha1` binary(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `run_id` (`run_id`),
  KEY `sensor_id` (`sensor_id`),
  KEY `floats_sha1` (`floats_sha1`),
  CONSTRAINT `sensor_data_to_run` FOREIGN KEY (`run_id`) REFERENCES `runs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `sensor_data_to_sensor` FOREIGN KEY (`sensor_id`) REFERENCES `sensors` (`id`) ON DELETE CASCADE
) COMMENT='
    Diagnostic sensor data collected from SauronX.
';

--
-- Table structure for table `sensors`
--

CREATE TABLE `sensors` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` varchar(250) DEFAULT NULL,
  `data_type` enum('byte','short','int','float','double','unsigned_byte','unsigned_short','unsigned_int','unsigned_float','unsigned_double','utf8_char','long','unsigned_long','other') NOT NULL,
  `blob_type` enum('assay_start','battery_start','every_n_milliseconds','every_n_frames','arbitrary') DEFAULT NULL,
  `n_between` int(10) unsigned DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) COMMENT='
    A diagnostic sensor on a Sauron.
';

--
-- Table structure for table `stimuli`
--

CREATE TABLE `stimuli` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `default_color` char(6) NOT NULL,
  `description` varchar(250) DEFAULT NULL,
  `analog` tinyint(1) NOT NULL DEFAULT 0,
  `rgb` binary(3) DEFAULT NULL,
  `wavelength_nm` smallint(5) unsigned DEFAULT NULL,
  `audio_file_id` smallint(5) unsigned DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  UNIQUE KEY `audio_file_id_unique` (`audio_file_id`),
  CONSTRAINT `stimulus_to_audio_file` FOREIGN KEY (`audio_file_id`) REFERENCES `audio_files` (`id`) ON DELETE CASCADE
) COMMENT='
    A single stimulus modulo strength (such as volume or PWM).
';

--
-- Table structure for table `stimulus_frames`
--

CREATE TABLE `stimulus_frames` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `assay_id` smallint(5) unsigned NOT NULL,
  `stimulus_id` smallint(5) unsigned NOT NULL,
  `frames` longblob NOT NULL COMMENT 'A sequence of signed bytes (-127 to 128) indicating the stimulus intensity (e.g. PWM) per millisecond.',
  `frames_sha1` binary(20) NOT NULL COMMENT 'The binary SHA-1 of the frames blob.',
  PRIMARY KEY (`id`),
  UNIQUE KEY `assay_id_stimulus_id` (`assay_id`,`stimulus_id`),
  KEY `assay_id` (`assay_id`),
  KEY `stimulus_id` (`stimulus_id`),
  KEY `frames_sha1` (`frames_sha1`),
  CONSTRAINT `stimulus_frames_to_assay` FOREIGN KEY (`assay_id`) REFERENCES `assays` (`id`) ON DELETE CASCADE,
  CONSTRAINT `stimulus_frames_to_stimulus` FOREIGN KEY (`stimulus_id`) REFERENCES `stimuli` (`id`)
) COMMENT='
    A sequence of frames for a single stimulus and assay specified as a sequence of values, one per millisecond.
';

--
-- Table structure for table `submission_params`
--

CREATE TABLE `submission_params` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `submission_id` mediumint(8) unsigned NOT NULL,
  `name` varchar(250) NOT NULL,
  `param_type` enum('n_fish','compound','dose','variant','dpf','group') NOT NULL,
  `value` varchar(4000) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `submission_name_unique` (`submission_id`,`name`),
  CONSTRAINT `submission_param_to_submission` FOREIGN KEY (`submission_id`) REFERENCES `submissions` (`id`) ON DELETE CASCADE
) COMMENT='
    A parameter for a template_well set in a single submission.
';

--
-- Table structure for table `submission_records`
--

CREATE TABLE `submission_records` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `submission_id` mediumint(8) unsigned NOT NULL,
  `task` varchar(30) DEFAULT NULL COMMENT 'A standard name of the task, such as "start run" or "start insert"',
  `feature_id` tinyint(3) unsigned DEFAULT NULL COMMENT 'If the task is to calculate a feature, specify the feature.',
  `failure` bool NOT NULL COMMENT 'True if the task failed.',
  `spawner_id` int(10) unsigned NULL COMMENT 'The task that spawned this one. If started by a user command, leave NULL.',
  `sauron_id` tinyint(3) unsigned NOT NULL COMMENT 'Should always inherit the Sauron that the data originally came from.',
  `datetime_modified` datetime NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `sauron_id` (`sauron_id`),
  KEY `submission_id` (`submission_id`),
  CONSTRAINT `submission_record_to_feature` FOREIGN KEY (`feature_id`) REFERENCES `features` (`id`) ON DELETE SET NULL,
  CONSTRAINT `submission_record_to_spawner` FOREIGN KEY (`spawner_id`) REFERENCES `submission_records` (`id`) ON DELETE SET NULL,
  CONSTRAINT `submission_record_to_sauron` FOREIGN KEY (`sauron_id`) REFERENCES `saurons` (`id`) ON DELETE SET NULL,
  CONSTRAINT `submission_record_to_submission` FOREIGN KEY (`submission_id`) REFERENCES `submissions` (`id`) ON DELETE CASCADE
) COMMENT='
    Tasks that have completed or failed in processing submissions and runs.
';

--
-- Table structure for table `submissions`
--

CREATE TABLE `submissions` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `lookup_hash` char(12) NOT NULL,
  `experiment_id` smallint(5) unsigned NOT NULL,
  `user_id` smallint(5) unsigned NOT NULL,
  `person_plated_id` smallint(5) unsigned NOT NULL,
  `continuing_id` mediumint(8) unsigned DEFAULT NULL,
  `datetime_plated` datetime NOT NULL,
  `datetime_dosed` datetime DEFAULT NULL,
  `acclimation_sec` int(10) unsigned DEFAULT NULL,
  `description` varchar(250) NOT NULL,
  `notes` mediumtext DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_hash_hex` (`lookup_hash`),
  KEY `submission_to_project` (`experiment_id`),
  KEY `submission_to_user` (`user_id`),
  KEY `submission_to_plate` (`continuing_id`),
  KEY `submission_to_person_plated` (`person_plated_id`),
  CONSTRAINT `matched_submission` FOREIGN KEY (`continuing_id`) REFERENCES `submissions` (`id`),
  CONSTRAINT `submission_to_person_plated` FOREIGN KEY (`person_plated_id`) REFERENCES `users` (`id`),
  CONSTRAINT `submission_to_project` FOREIGN KEY (`experiment_id`) REFERENCES `experiments` (`id`),
  CONSTRAINT `submission_to_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) COMMENT='
    A planned run filled out on the website.
';

--
-- Table structure for table `projects`
--

CREATE TABLE `projects` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `type_id` tinyint(3) unsigned DEFAULT NULL,
  `creator_id` smallint(5) unsigned NOT NULL,
  `description` varchar(10000) DEFAULT NULL,
  `reason` mediumtext DEFAULT NULL,
  `methods` mediumtext DEFAULT NULL,
  `active` tinyint(1) NOT NULL DEFAULT 1,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `creator_id` (`creator_id`),
  KEY `type_id` (`type_id`),
  CONSTRAINT `project_to_project_type` FOREIGN KEY (`type_id`) REFERENCES `project_types` (`id`),
  CONSTRAINT `project_to_user` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) COMMENT='
    A subset of a scientific project, such as a reference set of anxiolytics.
';

--
-- Table structure for table `suppliers`
--

CREATE TABLE `suppliers` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` varchar(250) DEFAULT NULL,
  `created` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) COMMENT='
    A supplier of a chemical, genetic construct, etc.
';

--
-- Table structure for table `template_assays`
--

CREATE TABLE `template_assays` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` varchar(10000) DEFAULT NULL,
  `author_id` smallint(5) unsigned DEFAULT NULL,
  `specializes` smallint(5) unsigned DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `author_index` (`author_id`),
  KEY `template_battery_specialization` (`specializes`),
  CONSTRAINT `template_assay_specialization` FOREIGN KEY (`specializes`) REFERENCES `template_assays` (`id`) ON DELETE SET NULL,
  CONSTRAINT `template_assay_to_user` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) COMMENT='
    An assay that has not been transformed into binary yet. These can contain parameters.
';

--
-- Table structure for table `template_plates`
--

CREATE TABLE `template_plates` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` varchar(10000) DEFAULT NULL,
  `plate_type_id` tinyint(3) unsigned NOT NULL,
  `author_id` smallint(5) unsigned NOT NULL,
  `hidden` tinyint(1) NOT NULL DEFAULT 0,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  `specializes_id` smallint(5) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `author_id` (`author_id`),
  KEY `specializes_id` (`specializes_id`),
  KEY `plate_type_id` (`plate_type_id`),
  CONSTRAINT `template_plate_specialization` FOREIGN KEY (`specializes_id`) REFERENCES `template_plates` (`id`) ON DELETE SET NULL,
  CONSTRAINT `template_plate_to_plate_type` FOREIGN KEY (`plate_type_id`) REFERENCES `plate_types` (`id`),
  CONSTRAINT `template_plate_to_user` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`)
) COMMENT='
    A parameterized plate layout.
';

--
-- Table structure for table `template_stimulus_frames`
--

CREATE TABLE `template_stimulus_frames` (
  `id` mediumint(6) unsigned NOT NULL AUTO_INCREMENT,
  `template_assay_id` smallint(5) unsigned NOT NULL,
  `range_expression` varchar(150) NOT NULL,
  `stimulus_id` smallint(5) unsigned NOT NULL,
  `value_expression` varchar(250) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `stimulus_index` (`stimulus_id`),
  KEY `template_battery` (`template_assay_id`),
  CONSTRAINT `template_frames_to_template_assay` FOREIGN KEY (`template_assay_id`) REFERENCES `template_assays` (`id`) ON DELETE CASCADE,
  CONSTRAINT `template_stimulus_frames_to_stimulus` FOREIGN KEY (`stimulus_id`) REFERENCES `stimuli` (`id`)
) COMMENT='
    Part of a template assay.
';

--
-- Table structure for table `template_treatments`
--

CREATE TABLE `template_treatments` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `template_plate_id` smallint(5) unsigned NOT NULL,
  `well_range_expression` varchar(100) NOT NULL,
  `batch_expression` varchar(250) NOT NULL,
  `dose_expression` varchar(200) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `template_plate_id` (`template_plate_id`),
  CONSTRAINT `template_well_to_template_plate` FOREIGN KEY (`template_plate_id`) REFERENCES `template_plates` (`id`) ON DELETE CASCADE
) COMMENT='
    Part of a template layout.
';

--
-- Table structure for table `template_wells`
--

CREATE TABLE `template_wells` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `template_plate_id` smallint(5) unsigned NOT NULL,
  `well_range_expression` varchar(255) NOT NULL,
  `control_type` tinyint(3) unsigned DEFAULT NULL,
  `n_expression` varchar(250) NOT NULL,
  `variant_expression` varchar(250) NOT NULL,
  `age_expression` varchar(255) NOT NULL,
  `group_expression` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tw_to_tp` (`template_plate_id`),
  KEY `template_well_to_control_type` (`control_type`),
  CONSTRAINT `template_well_to_control_type` FOREIGN KEY (`control_type`) REFERENCES `control_types` (`id`),
  CONSTRAINT `tw_to_tp` FOREIGN KEY (`template_plate_id`) REFERENCES `template_plates` (`id`) ON DELETE CASCADE
) COMMENT='
    Part of a template layout.
';

--
-- Table structure for table `transfer_plates`
--

CREATE TABLE `transfer_plates` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` varchar(250) DEFAULT NULL,
  `plate_type_id` tinyint(3) unsigned NOT NULL,
  `supplier_id` smallint(5) unsigned DEFAULT NULL,
  `parent_id` smallint(5) unsigned DEFAULT NULL,
  `dilution_factor_from_parent` double unsigned DEFAULT NULL,
  `initial_ul_per_well` double unsigned NOT NULL,
  `creator_id` smallint(5) unsigned NOT NULL,
  `datetime_created` datetime NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
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
) COMMENT='
    A mother plate containing compounds to be transferred.
';

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(20) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `write_access` tinyint(1) NOT NULL DEFAULT 1,
  `bcrypt_hash` char(60) DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `username_unique` (`username`),
  KEY `bcrypt_hash` (`bcrypt_hash`),
  KEY `first_name` (`first_name`),
  KEY `last_name` (`last_name`),
  KEY `write_access` (`write_access`)
) COMMENT='
    A person who can run and/or access data.
';

--
-- Table structure for table `well_features`
--

CREATE TABLE `well_features` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `well_id` mediumint(8) unsigned NOT NULL,
  `type_id` tinyint(3) unsigned NOT NULL,
  `floats` longblob NOT NULL,
  `sha1` binary(40) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `type_id` (`type_id`),
  KEY `sha1` (`sha1`),
  KEY `well_id` (`well_id`),
  CONSTRAINT `well_feature_to_type` FOREIGN KEY (`type_id`) REFERENCES `features` (`id`),
  CONSTRAINT `well_feature_to_well` FOREIGN KEY (`well_id`) REFERENCES `wells` (`id`) ON DELETE CASCADE
) COMMENT='
    A video feature computed on a well.
';

--
-- Table structure for table `well_treatments`
--

CREATE TABLE `well_treatments` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `well_id` mediumint(8) unsigned NOT NULL,
  `batch_id` mediumint(8) unsigned NOT NULL,
  `micromolar_dose` double unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `well_batch_unique` (`well_id`,`batch_id`),
  KEY `compound_id` (`batch_id`),
  KEY `well_id` (`well_id`),
  CONSTRAINT `well_treatment_to_batch` FOREIGN KEY (`batch_id`) REFERENCES `batches` (`id`),
  CONSTRAINT `well_treatment_to_well` FOREIGN KEY (`well_id`) REFERENCES `wells` (`id`) ON DELETE CASCADE
) COMMENT='
    Links compound batches to wells on a run of a plate.
';

--
-- Table structure for table `wells`
--

CREATE TABLE `wells` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `run_id` mediumint(8) unsigned NOT NULL,
  `well_index` smallint(5) unsigned NOT NULL,
  `control_type_id` tinyint(3) unsigned DEFAULT NULL,
  `variant_id` mediumint(8) unsigned DEFAULT NULL,
  `well_group` varchar(50) DEFAULT NULL COMMENT 'A flexible name for a subset of wells; for example to mark clutches.',
  `n` mediumint(9) NOT NULL DEFAULT 0 COMMENT 'In almost all cases, this should be the number of animals',
  `age` mediumint(8) unsigned DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `run_well_unique` (`run_id`,`well_index`),
  KEY `plate_id` (`run_id`),
  KEY `variant_id` (`variant_id`),
  KEY `well_group` (`well_group`),
  KEY `control_type_id` (`control_type_id`),
  KEY `n` (`n`),
  KEY `well_index` (`well_index`),
  CONSTRAINT `well_to_control_type` FOREIGN KEY (`control_type_id`) REFERENCES `control_types` (`id`),
  CONSTRAINT `well_to_genetic_variant` FOREIGN KEY (`variant_id`) REFERENCES `genetic_variants` (`id`),
  CONSTRAINT `well_to_run` FOREIGN KEY (`run_id`) REFERENCES `runs` (`id`) ON DELETE CASCADE
) COMMENT='
    A well on a run of a plate.
';
