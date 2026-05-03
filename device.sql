/*
 Navicat Premium Dump SQL

 Source Server         : mysql
 Source Server Type    : MySQL
 Source Server Version : 80011 (8.0.11)
 Source Host           : localhost:3306
 Source Schema         : device

 Target Server Type    : MySQL
 Target Server Version : 80011 (8.0.11)
 File Encoding         : 65001

 Date: 09/03/2026 16:15:40
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for caching
-- ----------------------------
DROP TABLE IF EXISTS `caching`;
CREATE TABLE `caching`  (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `dev_ID` int(11) NULL DEFAULT NULL,
  `Var_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `Data_type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `modbus_type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `modbus_device` int(11) NULL DEFAULT NULL,
  `modbus_addr` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `data_len` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `string_len` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `Decimal_digits` int(255) NULL DEFAULT NULL,
  PRIMARY KEY (`ID`) USING BTREE,
  INDEX `devid`(`dev_ID` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 89 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for dev
-- ----------------------------
DROP TABLE IF EXISTS `dev`;
CREATE TABLE `dev`  (
  `Id` int(11) NOT NULL AUTO_INCREMENT,
  `Devname` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `DevSerial` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `DevLocation` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `DevStatus` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `LatestOnline` datetime NULL DEFAULT NULL,
  `sendmodel` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `configdata` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `Baud` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `Changeflag` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `successflag` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`Id`) USING BTREE,
  INDEX `Id`(`Id` ASC) USING BTREE,
  INDEX `Id_2`(`Id` ASC) USING BTREE,
  INDEX `Id_3`(`Id` ASC) USING BTREE,
  INDEX `Id_4`(`Id` ASC) USING BTREE,
  INDEX `Id_5`(`Id` ASC) USING BTREE,
  INDEX `Id_6`(`Id` ASC) USING BTREE,
  INDEX `Id_7`(`Id` ASC) USING BTREE,
  INDEX `Id_8`(`Id` ASC) USING BTREE,
  INDEX `Id_9`(`Id` ASC) USING BTREE,
  INDEX `Id_10`(`Id` ASC) USING BTREE,
  INDEX `Id_11`(`Id` ASC) USING BTREE,
  INDEX `Id_12`(`Id` ASC) USING BTREE,
  INDEX `Id_13`(`Id` ASC) USING BTREE,
  INDEX `Id_14`(`Id` ASC) USING BTREE,
  INDEX `Id_15`(`Id` ASC) USING BTREE,
  INDEX `Id_16`(`Id` ASC) USING BTREE,
  INDEX `Id_17`(`Id` ASC) USING BTREE,
  INDEX `Id_18`(`Id` ASC) USING BTREE,
  INDEX `Id_19`(`Id` ASC) USING BTREE,
  INDEX `Id_20`(`Id` ASC) USING BTREE,
  INDEX `Id_21`(`Id` ASC) USING BTREE,
  INDEX `Id_22`(`Id` ASC) USING BTREE,
  INDEX `Id_23`(`Id` ASC) USING BTREE,
  INDEX `Id_24`(`Id` ASC) USING BTREE,
  INDEX `Id_25`(`Id` ASC) USING BTREE,
  INDEX `Id_26`(`Id` ASC) USING BTREE,
  INDEX `Id_27`(`Id` ASC) USING BTREE,
  INDEX `Id_28`(`Id` ASC) USING BTREE,
  INDEX `Id_29`(`Id` ASC) USING BTREE,
  INDEX `Id_30`(`Id` ASC) USING BTREE,
  INDEX `Id_31`(`Id` ASC) USING BTREE,
  INDEX `Id_32`(`Id` ASC) USING BTREE,
  INDEX `Id_33`(`Id` ASC) USING BTREE,
  INDEX `Id_34`(`Id` ASC) USING BTREE,
  INDEX `Id_35`(`Id` ASC) USING BTREE,
  INDEX `Id_36`(`Id` ASC) USING BTREE,
  INDEX `Id_37`(`Id` ASC) USING BTREE,
  INDEX `Id_38`(`Id` ASC) USING BTREE,
  INDEX `Id_39`(`Id` ASC) USING BTREE,
  INDEX `Id_40`(`Id` ASC) USING BTREE,
  INDEX `Id_41`(`Id` ASC) USING BTREE,
  INDEX `Id_42`(`Id` ASC) USING BTREE,
  INDEX `Id_43`(`Id` ASC) USING BTREE,
  INDEX `Id_44`(`Id` ASC) USING BTREE,
  INDEX `Id_45`(`Id` ASC) USING BTREE,
  INDEX `Id_46`(`Id` ASC) USING BTREE,
  INDEX `Id_47`(`Id` ASC) USING BTREE,
  INDEX `Id_48`(`Id` ASC) USING BTREE,
  INDEX `Id_49`(`Id` ASC) USING BTREE,
  INDEX `Id_50`(`Id` ASC) USING BTREE,
  INDEX `Id_51`(`Id` ASC) USING BTREE,
  INDEX `Id_52`(`Id` ASC) USING BTREE,
  INDEX `Id_53`(`Id` ASC) USING BTREE,
  INDEX `Id_54`(`Id` ASC) USING BTREE,
  INDEX `Id_55`(`Id` ASC) USING BTREE,
  INDEX `Id_56`(`Id` ASC) USING BTREE,
  INDEX `Id_57`(`Id` ASC) USING BTREE,
  INDEX `Id_58`(`Id` ASC) USING BTREE,
  INDEX `Id_59`(`Id` ASC) USING BTREE,
  INDEX `Id_60`(`Id` ASC) USING BTREE,
  INDEX `Id_61`(`Id` ASC) USING BTREE,
  INDEX `Id_62`(`Id` ASC) USING BTREE,
  INDEX `Id_63`(`Id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 19 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for user
-- ----------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user`  (
  `Id` int(11) NOT NULL AUTO_INCREMENT,
  `Username` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `Password` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `Nickname` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `Type` int(255) NULL DEFAULT NULL,
  PRIMARY KEY (`Id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for variables
-- ----------------------------
DROP TABLE IF EXISTS `variables`;
CREATE TABLE `variables`  (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `dev_ID` int(11) NULL DEFAULT NULL,
  `Var_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `Data_type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `modbus_type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `modbus_device` int(11) NULL DEFAULT NULL,
  `modbus_addr` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `data_len` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `string_len` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `Decimal_digits` int(255) NULL DEFAULT NULL,
  PRIMARY KEY (`ID`) USING BTREE,
  INDEX `ID`(`ID` ASC) USING BTREE,
  INDEX `ID_2`(`ID` ASC) USING BTREE,
  INDEX `ID_3`(`ID` ASC) USING BTREE,
  INDEX `dev_ID`(`dev_ID` ASC) USING BTREE,
  INDEX `dev_ID_2`(`dev_ID` ASC) USING BTREE,
  CONSTRAINT `devid` FOREIGN KEY (`dev_ID`) REFERENCES `dev` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 54 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- View structure for data
-- ----------------------------
DROP VIEW IF EXISTS `data`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `data` AS select `dev`.`DevSerial` AS `DevSerial`,`variables`.`dev_ID` AS `dev_ID`,`variables`.`modbus_type` AS `modbus_type`,`variables`.`modbus_device` AS `modbus_device`,`variables`.`modbus_addr` AS `modbus_addr` from (`dev` join `variables` on((`dev`.`Id` = `variables`.`dev_ID`)));

SET FOREIGN_KEY_CHECKS = 1;
