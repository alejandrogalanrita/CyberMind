-- Users table
CREATE TABLE users (
    id INT UNIQUE,
    email VARCHAR(255) PRIMARY KEY,
    user_name VARCHAR(255) NOT NULL,
    user_surname VARCHAR(255) NOT NULL,
    user_password VARCHAR(255) NOT NULL,
    role VARCHAR(255) DEFAULT 'usuario' NOT NULL,
    active BOOLEAN DEFAULT TRUE NOT NULL,
    
    refresh_token VARCHAR(512),
    refresh_token_expires_at DATETIME,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE projects (
    email VARCHAR(255) NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    about TEXT,
    file_name VARCHAR(255),
    file_data LONGBLOB,
    report_name VARCHAR(255),
    report_data LONGBLOB,
    report_reasoning LONGBLOB,
    creation_date DATETIME NOT NULL,
    modification_date DATETIME NOT NULL,
    in_process BOOLEAN DEFAULT FALSE, -- Indicates if the project is currently being processed due to the resource limit of the demo
    max_total_vulns FLOAT,
    min_fixable_ratio FLOAT, 
    max_severity_level FLOAT,
    composite_score FLOAT,
    PRIMARY KEY (email, project_name)
);

-- Deleted Projects table
CREATE TABLE deleted_projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    about TEXT,
    file_name VARCHAR(255),
    file_data LONGBLOB,
    report_name VARCHAR(255),
    report_data LONGBLOB,
    report_reasoning LONGBLOB,
    creation_date DATETIME NOT NULL,
    deletion_date DATETIME NOT NULL,
    max_total_vulns FLOAT,
    min_fixable_ratio FLOAT, 
    max_severity_level FLOAT,
    composite_score FLOAT
);

-- Chat History table
CREATE TABLE chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- CVEs table
CREATE TABLE cves (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cve_id VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    published_date DATETIME,
    last_modified_date DATETIME,
    cvss_score FLOAT,
    vector_string VARCHAR(100),
    severity VARCHAR(20),
    cwe_id VARCHAR(20),
    embedding LONGBLOB -- JSON-encoded float list stored as BLOB
);

-- Logs table
CREATE TABLE log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    details TEXT NOT NULL
);

-- Alert permissions table
CREATE TABLE alert_permits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    alert_method VARCHAR(50) NOT NULL,
    alert_frequency VARCHAR(50) DEFAULT 'DAILY' NOT NULL,
    alert_enabled BOOLEAN DEFAULT TRUE NOT NULL
);

CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    notification_title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    project_name VARCHAR(255) NOT NULL
);



-- Create application-specific users
CREATE USER 'web' IDENTIFIED BY 'web_pass';
CREATE USER 'api_login' IDENTIFIED BY 'api_login_pass';
CREATE USER 'api_db' IDENTIFIED BY 'api_db_pass';
CREATE USER 'api_chat' IDENTIFIED BY 'api_chat_pass';
CREATE USER 'api_alert' IDENTIFIED BY 'api_alert_pass';
CREATE USER 'logs' IDENTIFIED BY 'logs_pass';

-- Permissions for web user: only access to users and projects tables
GRANT SELECT ON flask_database.users TO 'web';

-- Permissions for api_login: only access users table
GRANT SELECT ON flask_database.users TO 'api_login';

-- Permissions for api_db: access to users and projects
GRANT SELECT, INSERT, UPDATE, DELETE ON flask_database.users TO 'api_db';
GRANT SELECT, INSERT, UPDATE, DELETE ON flask_database.projects TO 'api_db';
GRANT SELECT, INSERT, UPDATE, DELETE ON flask_database.deleted_projects TO 'api_db';
GRANT SELECT ON flask_database.cves TO 'api_db';
GRANT SELECT, INSERT, UPDATE, DELETE ON flask_database.notifications TO 'api_db';

-- Permissions for api_chat: access to projects and cves
GRANT SELECT, UPDATE ON flask_database.projects TO 'api_chat';
GRANT SELECT, INSERT, UPDATE, DELETE ON flask_database.chat_history TO 'api_chat';
GRANT SELECT ON flask_database.cves TO 'api_chat';

-- Permissions for api_alert: access to alert permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON flask_database.alert_permits TO 'api_alert';
GRANT SELECT, INSERT ON flask_database.notifications TO 'api_alert';

-- Permissions for logs: access to logs
GRANT SELECT, INSERT ON flask_database.log TO 'logs';

-- Permissions for admin user
GRANT ALL PRIVILEGES ON flask_database.* TO 'admin';

-- Finalize
FLUSH PRIVILEGES;

INSERT INTO cves (cve_id, description, published_date, last_modified_date, cvss_score, vector_string, severity, cwe_id, embedding) VALUES
('CVE-1999-0095', 'The debug command in Sendmail is enabled, allowing attackers to execute commands as root.', '1988-10-01 04:00:00', '2025-04-03 01:03:51', 10.0, 'AV:N/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-0082', 'CWD ~root command in ftpd allows root access.', '1988-11-11 05:00:00', '2025-04-03 01:03:51', 10.0, 'AV:N/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1471', 'Buffer overflow in passwd in BSD based operating systems 4.3 and earlier allows local users to gain root privileges by specifying a long shell or GECOS field.', '1989-01-01 05:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1122', 'Vulnerability in restore in SunOS 4.0.3 and earlier allows local users to gain privileges.', '1989-07-26 04:00:00', '2025-04-03 01:03:51', 4.6, 'AV:L/AC:L/Au:N/C:P/I:P/A:P', 'MEDIUM', 'NVD-CWE-Other', NULL),
('CVE-1999-1467', 'Vulnerability in rcp on SunOS 4.0.x allows remote attackers from trusted hosts to execute arbitrary commands as root, possibly related to the configuration of the nobody user.', '1989-10-26 04:00:00', '2025-04-03 01:03:51', 10.0, 'AV:N/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1506', 'Vulnerability in SMI Sendmail 4.0 and earlier, on SunOS up to 4.0.3, allows remote attackers to access user bin.', '1990-01-29 05:00:00', '2025-04-03 01:03:51', 7.5, 'AV:N/AC:L/Au:N/C:P/I:P/A:P', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-0084', 'Certain NFS servers allow users to use mknod to gain privileges by creating a writable kmem device and setting the UID to 0.', '1990-05-01 04:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-2000-0388', 'Buffer overflow in FreeBSD libmytinfo library allows local users to execute commands via a long TERMCAP environmental variable.', '1990-05-09 04:00:00', '2025-04-03 01:03:51', 7.5, 'AV:N/AC:L/Au:N/C:P/I:P/A:P', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-0209', 'The SunView (SunTools) selection_svc facility allows remote users to read files.', '1990-08-14 04:00:00', '2025-04-03 01:03:51', 5.0, 'AV:N/AC:L/Au:N/C:P/I:N/A:N', 'MEDIUM', 'NVD-CWE-Other', NULL),
('CVE-1999-1198', 'BuildDisk program on NeXT systems before 2.0 does not prompt users for the root password, which allows local users to gain root privileges.', '1990-10-03 04:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1391', 'Vulnerability in NeXT 1.0a and 1.0 with publicly accessible printers allows local users to gain privileges via a combination of the npd program and weak directory permissions.', '1990-10-03 04:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1392', 'Vulnerability in restore0.9 installation script in NeXT 1.0a and 1.0 allows local users to gain root privileges.', '1990-10-03 04:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1057', 'VMS 4.0 through 5.3 allows local users to gain privileges via the ANALYZE/PROCESS_DUMP dcl command.', '1990-10-25 04:00:00', '2025-04-03 01:03:51', 4.6, 'AV:L/AC:L/Au:N/C:P/I:P/A:P', 'MEDIUM', 'NVD-CWE-Other', NULL),
('CVE-1999-1554', '/usr/sbin/Mail on SGI IRIX 3.3 and 3.3.1 does not properly set the group ID to the group ID of the user who started Mail, which allows local users to read the mail of other users.', '1990-10-31 05:00:00', '2025-04-03 01:03:51', 2.1, 'AV:L/AC:L/Au:N/C:P/I:N/A:N', 'LOW', 'NVD-CWE-Other', NULL),
('CVE-1999-1197', 'TIOCCONS in SunOS 4.1.1 does not properly check the permissions of a user who tries to redirect console output and input, which could allow a local user to gain privileges.', '1990-12-20 05:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1115', 'Vulnerability in the /etc/suid_exec program in HP Apollo Domain/OS sr10.2 and sr10.3 beta, related to the Korn Shell (ksh).', '1990-12-31 05:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1258', 'rpc.pwdauthd in SunOS 4.1.1 and earlier does not properly prevent remote access to the daemon, which allows remote attackers to obtain sensitive system information.', '1991-01-15 05:00:00', '2025-04-03 01:03:51', 5.0, 'AV:N/AC:L/Au:N/C:P/I:N/A:N', 'MEDIUM', 'NVD-CWE-Other', NULL),
('CVE-1999-1438', 'Vulnerability in /bin/mail in SunOS 4.1.1 and earlier allows local users to gain root privileges via certain command line arguments.', '1991-02-22 05:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1211', 'Vulnerability in in.telnetd in SunOS 4.1.1 and earlier allows local users to gain root privileges.', '1991-03-27 05:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1212', 'Vulnerability in in.rlogind in SunOS 4.0.3 and 4.0.3c allows local users to gain root privileges.', '1991-03-27 05:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1194', 'chroot in Digital Ultrix 4.1 and 4.0 is insecurely installed, which allows local users to gain privileges.', '1991-05-01 04:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1193', 'The "me" user in NeXT NeXTstep 2.1 and earlier has wheel group privileges, which could allow the me user to use the su command to become root.', '1991-05-14 04:00:00', '2025-04-03 01:03:51', 10.0, 'AV:N/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1123', 'The installation of Sun Source (sunsrc) tapes allows local users to gain root privileges via setuid root programs (1) makeinstall or (2) winstall.', '1991-05-20 04:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1034', 'Vulnerability in login in AT&T System V Release 4 allows local users to gain privileges.', '1991-05-23 04:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1415', 'Vulnerability in /usr/bin/mail in DEC ULTRIX before 4.2 allows local users to gain privileges.', '1991-08-23 04:00:00', '2025-04-03 01:03:51', 4.6, 'AV:L/AC:L/Au:N/C:P/I:P/A:P', 'MEDIUM', 'NVD-CWE-Other', NULL),
('CVE-1999-1090', 'The default configuration of NCSA Telnet package for Macintosh and PC enables FTP, even though it does not include an "ftp=yes" line, which allows remote attackers to read and modify arbitrary files.', '1991-09-10 04:00:00', '2025-04-03 01:03:51', 7.5, 'AV:N/AC:L/Au:N/C:P/I:P/A:P', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-0498', 'TFTP is not running in a restricted directory, allowing a remote attacker to access sensitive information such as password files.', '1991-09-27 04:00:00', '2025-04-03 01:03:51', 10.0, 'AV:N/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1468', 'rdist in various UNIX systems uses popen to execute sendmail, which allows local users to gain root privileges by modifying the IFS (Internal Field Separator) variable.', '1991-10-22 04:00:00', '2025-04-03 01:03:51', 6.2, 'AV:L/AC:H/Au:N/C:C/I:C/A:C', 'MEDIUM', 'NVD-CWE-Other', NULL),
('CVE-1999-0167', 'In SunOS, NFS file handles could be guessed, giving unauthorized access to the exported file system.', '1991-12-06 05:00:00', '2025-04-03 01:03:51', 4.6, 'AV:L/AC:L/Au:N/C:P/I:P/A:P', 'MEDIUM', 'NVD-CWE-Other', NULL),
('CVE-1999-1493', 'Vulnerability in crp in Hewlett Packard Apollo Domain OS SR10 through SR10.3 allows remote attackers to gain root privileges via insecure system calls, (1) pad_$dm_cmd and (2) pad_$def_pfk().', '1991-12-18 05:00:00', '2025-04-03 01:03:51', 10.0, 'AV:N/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1032', 'Vulnerability in LAT/Telnet Gateway (lattelnet) on Ultrix 4.1 and 4.2 allows attackers to gain root privileges.', '1991-12-31 05:00:00', '2025-04-03 01:03:51', 10.0, 'AV:N/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1059', 'Vulnerability in rexec daemon (rexecd) in AT&T TCP/IP 4.0 for various SVR4 systems allows remote attackers to execute arbitrary commands.', '1992-02-25 05:00:00', '2025-04-03 01:03:51', 10.0, 'AV:N/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-0627', 'The rexd service is running, which uses weak authentication that can allow an attacker to execute commands.', '1992-03-01 05:00:00', '2025-04-03 01:03:51', 0.0, 'AV:N/AC:L/Au:N/C:N/I:N/A:N', 'LOW', 'NVD-CWE-Other', NULL),
('CVE-1999-1121', 'The default configuration for UUCP in AIX before 3.2 allows local users to gain root privileges.', '1992-03-19 05:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-0117', 'AIX passwd allows local users to gain root access.', '1992-03-31 05:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1119', 'FTP installation script anon.ftp in AIX insecurely configures anonymous FTP, which allows remote attackers to execute arbitrary commands.', '1992-04-27 04:00:00', '2025-04-03 01:03:51', 10.0, 'AV:N/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1142', 'SunOS 4.1.2 and earlier allows local users to gain privileges via "LD_*" environmental variables to certain dynamically linked setuid or setgid programs such as (1) login, (2) su, or (3) sendmail, that change the real and effective user ids to the same user.', '1992-05-27 04:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-0168', 'The portmapper may act as a proxy and redirect service requests from an attacker, making the request appear to come from the local host, possibly bypassing authentication that would otherwise have taken place.  For example, NFS file systems could be mounted through the portmapper despite export restrictions.', '1992-06-04 04:00:00', '2025-04-03 01:03:51', 7.5, 'AV:N/AC:L/Au:N/C:P/I:P/A:P', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-0214', 'Denial of service by sending forged ICMP unreachable packets.', '1992-07-21 04:00:00', '2025-04-03 01:03:51', 10.0, 'AV:N/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1396', 'Vulnerability in integer multiplication emulation code on SPARC architectures for SunOS 4.1 through 4.1.2 allows local users to gain root access or cause a denial of service (crash).', '1992-07-21 04:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1395', 'Vulnerability in Monitor utility (SYS$SHARE:SPISHR.EXE) in VMS 5.0 through 5.4-2 allows local users to gain privileges.', '1992-11-17 05:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1306', 'Cisco IOS 9.1 and earlier does not properly handle extended IP access lists when the IP route cache is enabled and the "established" keyword is set, which could allow attackers to bypass filters.', '1992-12-10 05:00:00', '2025-04-03 01:03:51', 7.5, 'AV:N/AC:L/Au:N/C:P/I:P/A:P', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1466', 'Vulnerability in Cisco routers versions 8.2 through 9.1 allows remote attackers to bypass access control lists when extended IP access lists are used on certain interfaces, the IP route cache is enabled, and the access list uses the "established" keyword.', '1992-12-10 05:00:00', '2025-04-03 01:03:51', 7.5, 'AV:N/AC:L/Au:N/C:P/I:P/A:P', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1021', 'NFS on SunOS 4.1 through 4.1.2 ignores the high order 16 bits in a 32 bit UID, which allows a local user to gain root access if the lower 16 bits are set to 0, as fixed by the NFS jumbo patch upgrade.', '1992-12-30 05:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1056', 'Rejected reason: DO NOT USE THIS CANDIDATE NUMBER.  ConsultIDs: CVE-1999-1395.  Reason: This candidate is a duplicate of CVE-1999-1395.  Notes: All CVE users should reference CVE-1999-1395 instead of this candidate.  All references and descriptions in this candidate have been removed to prevent accidental usage', '1992-12-31 05:00:00', '2023-11-07 01:55:06', NULL, NULL, NULL, NULL, NULL),
('CVE-1999-0312', 'HP ypbind allows attackers with root privileges to modify NIS data.', '1993-01-13 05:00:00', '2025-04-03 01:03:51', 5.0, 'AV:N/AC:L/Au:N/C:P/I:N/A:N', 'MEDIUM', 'NVD-CWE-Other', NULL),
('CVE-1999-1507', 'Sun SunOS 4.1 through 4.1.3 allows local attackers to gain root access via insecure permissions on files and directories such as crash.', '1993-02-03 05:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1218', 'Vulnerability in finger in Commodore Amiga UNIX 2.1p2a and earlier allows local users to read arbitrary files.', '1993-02-18 05:00:00', '2025-04-03 01:03:51', 2.1, 'AV:L/AC:L/Au:N/C:P/I:N/A:N', 'LOW', 'NVD-CWE-Other', NULL),
('CVE-1999-1312', 'Vulnerability in DEC OpenVMS VAX 5.5-2 through 5.0, and OpenVMS AXP 1.0, allows local users to gain system privileges.', '1993-02-24 05:00:00', '2025-04-03 01:03:51', 7.2, 'AV:L/AC:L/Au:N/C:C/I:C/A:C', 'HIGH', 'NVD-CWE-Other', NULL),
('CVE-1999-1216', 'Cisco routers 9.17 and earlier allow remote attackers to bypass security restrictions via certain IP source routed packets that should normally be denied using the "no ip source-route" command.', '1993-04-22 04:00:00', '2025-04-03 01:03:51', 7.5, 'AV:N/AC:L/Au:N/C:P/I:P/A:P', 'HIGH', 'NVD-CWE-Other', NULL);
