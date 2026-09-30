#!/bin/sh
set -e
submit app/jcl/RPTJOB.jcl
submit app/jcl/UPDJOB.jcl
submit app/jcl/DBJOB.jcl
