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
  `Decimal_digits` int(11) NULL DEFAULT NULL,
  `scale` float NULL DEFAULT 1.0 COMMENT '缩放因子',
  `offset` float NULL DEFAULT 0 COMMENT '偏移量',
  `reg_count` int(11) NULL DEFAULT 1 COMMENT '寄存器数量',
  `byte_order` varchar(10) NULL DEFAULT 'ABCD' COMMENT '字节序',
  `unit` varchar(20) NULL DEFAULT '' COMMENT '单位',
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
  PRIMARY KEY (`Id`) USING BTREE
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
  `Type` int(11) NULL DEFAULT NULL,
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
  `Decimal_digits` int(11) NULL DEFAULT NULL,
  `scale` float NULL DEFAULT 1.0 COMMENT '缩放因子',
  `offset` float NULL DEFAULT 0 COMMENT '偏移量',
  `reg_count` int(11) NULL DEFAULT 1 COMMENT '寄存器数量',
  `byte_order` varchar(10) NULL DEFAULT 'ABCD' COMMENT '字节序',
  `unit` varchar(20) NULL DEFAULT '' COMMENT '单位',
  PRIMARY KEY (`ID`) USING BTREE,
  INDEX `dev_ID`(`dev_ID` ASC) USING BTREE,
  CONSTRAINT `devid` FOREIGN KEY (`dev_ID`) REFERENCES `dev` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 54 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- View structure for data
-- ----------------------------
DROP VIEW IF EXISTS `data`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `data` AS select `dev`.`DevSerial` AS `DevSerial`,`variables`.`dev_ID` AS `dev_ID`,`variables`.`modbus_type` AS `modbus_type`,`variables`.`modbus_device` AS `modbus_device`,`variables`.`modbus_addr` AS `modbus_addr` from (`dev` join `variables` on((`dev`.`Id` = `variables`.`dev_ID`)));

SET FOREIGN_KEY_CHECKS = 1;
