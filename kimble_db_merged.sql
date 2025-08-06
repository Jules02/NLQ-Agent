-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: kimble_db
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `employees`
--

DROP TABLE IF EXISTS `employees`;
CREATE TABLE `employees` (
  `employee_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `role` varchar(50) NOT NULL,
  `leave_balance` int DEFAULT '20',
  `manager_id` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`employee_id`),
  UNIQUE KEY `email` (`email`),
  KEY `manager_id` (`manager_id`),
  CONSTRAINT `employees_ibfk_1` FOREIGN KEY (`manager_id`) REFERENCES `employees` (`employee_id`)
) ENGINE=InnoDB AUTO_INCREMENT=101 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `projects`
--

DROP TABLE IF EXISTS `projects`;
CREATE TABLE `projects` (
  `project_id` int NOT NULL AUTO_INCREMENT,
  `project_name` varchar(255) NOT NULL,
  `department` varchar(100) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`project_id`),
  UNIQUE KEY `project_name` (`project_name`)
) ENGINE=InnoDB AUTO_INCREMENT=101 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `project_assignments`
--

DROP TABLE IF EXISTS `project_assignments`;
CREATE TABLE `project_assignments` (
  `assignment_id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `project_id` int NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date DEFAULT NULL,
  PRIMARY KEY (`assignment_id`),
  UNIQUE KEY `employee_id` (`employee_id`,`project_id`,`start_date`),
  KEY `project_id` (`project_id`),
  CONSTRAINT `project_assignments_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`),
  CONSTRAINT `project_assignments_ibfk_2` FOREIGN KEY (`project_id`) REFERENCES `projects` (`project_id`)
) ENGINE=InnoDB AUTO_INCREMENT=101 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `activity_reports`
--

DROP TABLE IF EXISTS `activity_reports`;
CREATE TABLE `activity_reports` (
  `report_id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `project_id` int NOT NULL,
  `date` date NOT NULL,
  `hours` int NOT NULL,
  `status` varchar(50) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`report_id`),
  KEY `employee_id` (`employee_id`),
  KEY `project_id` (`project_id`),
  CONSTRAINT `activity_reports_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`),
  CONSTRAINT `activity_reports_ibfk_2` FOREIGN KEY (`project_id`) REFERENCES `projects` (`project_id`)
) ENGINE=InnoDB AUTO_INCREMENT=51 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `leave_requests`
--

DROP TABLE IF EXISTS `leave_requests`;
CREATE TABLE `leave_requests` (
  `leave_id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `manager_id` int NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `type` varchar(50) NOT NULL,
  `status` varchar(50) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`leave_id`),
  KEY `employee_id` (`employee_id`),
  KEY `manager_id` (`manager_id`),
  CONSTRAINT `leave_requests_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`),
  CONSTRAINT `leave_requests_ibfk_2` FOREIGN KEY (`manager_id`) REFERENCES `employees` (`employee_id`)
) ENGINE=InnoDB AUTO_INCREMENT=51 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `presence`
--

DROP TABLE IF EXISTS `presence`;
CREATE TABLE `presence` (
  `presence_id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `date` date NOT NULL,
  `status` varchar(50) NOT NULL,
  PRIMARY KEY (`presence_id`),
  UNIQUE KEY `employee_id` (`employee_id`,`date`),
  CONSTRAINT `presence_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`)
) ENGINE=InnoDB AUTO_INCREMENT=101 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for tables
--

-- Insert sample data for employees
INSERT INTO `employees` VALUES 
(51,'Alice Brown','alice.brown@kimble.com','CEO',30,NULL,'2025-07-30 10:29:52'),
(52,'Adam Bryan','manager1@kimble.com','Manager',20,51,'2025-07-30 10:29:52'),
(53,'Jacob Lee','manager2@kimble.com','Manager',27,51,'2025-07-30 10:29:52'),
(54,'Candice Martinez','manager3@kimble.com','Manager',23,51,'2025-07-30 10:29:52'),
(55,'Justin Thompson','manager4@kimble.com','Manager',23,51,'2025-07-30 10:29:52'),
(56,'Heather Rubio','manager5@kimble.com','Manager',24,51,'2025-07-30 10:29:53'),
(57,'William Jenkins','employee1@kimble.com','Employee',25,55,'2025-07-30 10:29:53'),
(58,'Brittany Ball','employee2@kimble.com','Employee',20,52,'2025-07-30 10:29:53'),
(59,'Glenn Johnson','employee3@kimble.com','Employee',20,55,'2025-07-30 10:29:53'),
(60,'Walter Irwin','employee4@kimble.com','Employee',21,54,'2025-07-30 10:29:53');

-- Insert sample data for projects
INSERT INTO `projects` VALUES 
(51,'Project A1','Research','2025-07-30 10:29:53'),
(52,'Project B1','Engineering','2025-07-30 10:29:53'),
(53,'Project C1','Operations','2025-07-30 10:29:53'),
(54,'Project D1','Engineering','2025-07-30 10:29:53'),
(55,'Project E1','Research','2025-07-30 10:29:53'),
(56,'Project F1','Marketing','2025-07-30 10:29:53'),
(57,'Project G1','Research','2025-07-30 10:29:53'),
(58,'Project H1','Sales','2025-07-30 10:29:53'),
(59,'Project I1','Research','2025-07-30 10:29:53'),
(60,'Project J1','Sales','2025-07-30 10:29:53');

-- Insert sample data for project_assignments
INSERT INTO `project_assignments` VALUES 
(51,52,70,'2025-07-12',NULL),
(52,52,59,'2025-07-01',NULL),
(53,52,90,'2025-07-10',NULL),
(54,53,98,'2025-07-18',NULL),
(55,53,76,'2025-07-17',NULL),
(56,54,69,'2025-07-05','2025-07-01'),
(57,55,75,'2025-07-27',NULL),
(58,56,89,'2025-07-19',NULL),
(59,56,64,'2025-07-09',NULL),
(60,56,92,'2025-07-21',NULL);

-- Insert sample data for activity_reports
INSERT INTO `activity_reports` VALUES 
(1,52,70,'2025-07-23',5,'Draft','2025-07-30 10:29:53'),
(2,52,90,'2025-07-23',4,'Approved','2025-07-30 10:29:53'),
(3,52,59,'2025-07-24',6,'Rejected','2025-07-30 10:29:53'),
(4,52,90,'2025-07-24',8,'Draft','2025-07-30 10:29:53'),
(5,52,70,'2025-07-25',8,'Rejected','2025-07-30 10:29:53'),
(6,52,90,'2025-07-25',7,'Approved','2025-07-30 10:29:53'),
(7,52,70,'2025-07-26',8,'Rejected','2025-07-30 10:29:53'),
(8,52,90,'2025-07-26',7,'Draft','2025-07-30 10:29:53'),
(9,53,98,'2025-07-24',6,'Rejected','2025-07-30 10:29:53'),
(10,53,98,'2025-07-25',4,'Submitted','2025-07-30 10:29:53');

-- Insert sample data for leave_requests
INSERT INTO `leave_requests` VALUES 
(1,53,51,'2025-07-02','2025-07-03','Vacation','Rejected','2025-07-30 10:29:53'),
(2,54,51,'2025-07-05','2025-07-09','Vacation','Pending','2025-07-30 10:29:53'),
(3,54,51,'2025-07-23','2025-07-26','Personal','Approved','2025-07-30 10:29:53'),
(4,56,51,'2025-07-08','2025-07-09','Personal','Approved','2025-07-30 10:29:53'),
(5,56,51,'2025-07-08','2025-07-09','Disruption','Pending','2025-07-30 10:29:53'),
(6,58,52,'2025-07-29','2025-07-30','Personal','Pending','2025-07-30 10:29:53'),
(7,60,54,'2025-07-29','2025-07-31','Personal','Pending','2025-07-30 10:29:53'),
(8,61,53,'2025-07-01','2025-07-04','Personal','Pending','2025-07-30 10:29:53'),
(9,62,53,'2025-07-28','2025-07-31','Personal','Approved','2025-07-30 10:29:53'),
(10,64,52,'2025-07-23','2025-07-24','Disruption','Rejected','2025-07-30 10:29:53');

-- Insert sample data for presence
INSERT INTO `presence` VALUES 
(51,52,'2025-07-23','On Leave'),
(52,52,'2025-07-24','Absent'),
(53,52,'2025-07-25','Present'),
(54,52,'2025-07-26','Present'),
(55,52,'2025-07-27','On Leave'),
(56,52,'2025-07-28','Absent'),
(57,52,'2025-07-29','On Leave'),
(58,53,'2025-07-23','Absent'),
(59,53,'2025-07-24','Absent'),
(60,53,'2025-07-25','Present');

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
