import time

def _all_true(vec):
    for v in vec:
        if not v:
            return False
    return True

def move_abs(posins, moveins, newpos, startstep=4, maxstep=128, minstep=1, delay=0.05):
    """
    move_abs, generic function to control read-out/positioner combo

    Input:
        posins: position reading instrument (should implement 'get_position')
        moveins: position control instrument (should implement 'step')
        newpos: new position vector, the length of this vector sets which
                channels will be used.
        startstep: start steps to use
        maxstep: maximum steps
        minstep: minimum steps for fine position
        delay: time delay after each step
    """

    channels = len(newpos)
    pos = posins.get_position()
    delta = [newpos[i] - pos[i] for i in range(channels)]
    dist = [abs(delta[i]) for i in range(channels)]
    hold = [False for i in range(channels)]
    increase_steps = True
    print 'move_abs(): start pos = %r, delta = %r, dist = %r' % \
        (repr(pos), repr(delta), repr(dist))

    steps = [-misc.sign(delta[i]) * startstep for i in range(channels)]

    j = 0
    while True and j < 1000:

        # Move
        for i in range(channels):
            if not hold[i]:
                moveins.step(i, steps[i])
        time.sleep(0.05)

        pos2 = posins.get_position()
        delta2 = [newpos[i] - pos2[i] for i in range(channels)]
        dist2 = [abs(deltar[i]) for i in range(channels)]
        print 'move_abs(): pos = %r, delta2 = %r' % \
            (repr(pos2), repr(delta2))

        if increase_steps:
            for i in range(channels):
                if not hold[i]:
                    if misc.sign(delta2[i]) != misc.sign(delta[i]):
                        hold[i] = True
                    elif abs(steps[i]) != maxstep:
                        print 'move_abs(): increasing stepsize for ch%d' % i
                        steps[i] = misc.sign(delta2[i]) * min(abs(steps[i]) * 2, maxstep)

            if _all_true(hold):
                increase_steps = False
                hold = [False for i in range(channels)]

        # Immediately reverse if we moved too far
        if not increase_steps:
            for i in range(channels):
                if not hold[i]:
                    if misc.sign(delta2[i]) != misc.sign(delta[i]):
                        if abs(steps[i]) == minstep:
                            hold[i] = True
                        else:
                            steps[i] = int(misc.sign(delta2[i]) * max(round(abs(steps[i]) / 2), minstep))

            if _all_true(hold):
                print 'Moved to position!'
                break

            # Remember relative position
            delta = delta2

        j += 1

    print 'move_abs(): Finished'

def scan_simple(ins):
    pass

