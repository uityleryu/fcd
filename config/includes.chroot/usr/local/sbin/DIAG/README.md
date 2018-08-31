# UPyDiag

**UPyDiag** is a python project to deal with a generic diagnostic program for embedded system.

## About
**UPyDiag** is a generic diagnostic program provides an interactive command line shell to verify and test the H/W components easily.

### Source Folder Structure
```
- UPyDiag/
```

### Setup environment
$ export PYTHONPATH="/usr/local/sbin/ubntlib/"

## Running
For us_flex example:
$ python3 upydiag.py us_flex

or you can assign PYTHONPATH in command
$ PYTHONPATH="/usr/local/sbin/ubntlib/" upydiag.py us_flex

you can log all operation in diag shell
$ script -f -c "python3 -u upydiag.py us_flex" diag_op.log

### Usage

```
$ python3 upydiag.py

Usage:

  upydiag.py <machine>

<machine>: Supported models which described by
            machine/<machine>/<machine>.json

