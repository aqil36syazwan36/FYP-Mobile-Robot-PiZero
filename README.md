# FYP Mobile Robot - Raspberry Pi Zero W Low-Level Controller

This repository contains the Raspberry Pi Zero W low-level controller code for my FYP mobile robot.

## Function

The Raspberry Pi Zero W handles:

- PCA9685 PWM driver
- 2x BTS7960 motor drivers
- 4 DC motor encoders
- TCP JSON communication with Raspberry Pi 5

## Main Program

Main file:

microros_ws/motor_server.py

The motor server listens on:

0.0.0.0:65432

The Raspberry Pi 5 ROS 2 bridge connects using:

rp0w.local:65432

## Auto-Start Service

Systemd service file:

systemd/robot_motor_server.service

Install on Pi Zero W:

sudo cp systemd/robot_motor_server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable robot_motor_server.service
sudo systemctl start robot_motor_server.service

Check status:

systemctl status robot_motor_server.service --no-pager

## Current Status

- PCA9685 detected
- BTS7960 motor control working
- 4 encoder feedback working
- TCP communication with Raspberry Pi 5 working
- ROS 2 cmd_vel bridge working
- Auto-start service working after reboot
