# Readify Environment


###
### Functions
###

### This function is activates an environment prepared with `etc/std.reqs`
readify() {
    ### Figure out the absolute path to Readify based on where this file 
    ### `readifyenv.sh` lives
    export READIFY_ENV_PATH=$(cd $(dirname $READIFY_ENV_SCRIPT); pwd)

    ### Set project directory path
    export READIFY_DIR=$(dirname $READIFY_ENV_PATH)

    ### Hardcode paths to the apps
    export PREV_PYTHONPATH=$PYTHONPATH

    ### Update PYTHONPATH with a call to arbresetapppaths
    PYTHONPATH=$PREV_PYTHONPATH
    export PYTHONPATH="$READIFY_DIR:$PYTHONPATH"
}

### This function is activates an environment prepared with `etc/dev.reqs`
readify_dev() {
    readify
    PROJECT_DIR=$(dirname $READIFY_DIR)
    BRUBECK_DIR=$PROJECT_DIR/brubeck
    DICTSHIELD_DIR=$PROJECT_DIR/dictshield
    export PYTHONPATH=$BRUBECK_DIR:$DICTSHIELD_DIR:$PYTHONPATH
}

### Deactivates an environment by returning paths back to normal
readify_deactivate() {
    export PYTHONPATH=$PREV_PYTHONPATH
    unset PREV_PYTHONPATH
    unset READIFY_ENV_PATH
    unset READIFY_DIR
    \rm -f api_send
    \rm -f api_recv
    \rm -f web_send
    \rm -f web_recv
}

### Shortcut for cd'ing to project dir
readify_dir () {
    \cd $READIFY_DIR
}


###
### Environment Adjustments
###

### `source`ing this file causes anything below here to occur
export READIFY_ENV_SCRIPT=${BASH_SOURCE[@]}
