import math

diff_x = 50
diff_y = -50
length = int(math.dist((0, 0), (diff_x, diff_y)))


def accelerate_decelerate(k, total_steps):
    max_speed = 9
    acceleration_phase = total_steps // 2
    deceleration_phase = total_steps - acceleration_phase

    if k < acceleration_phase:
        speed = (k + 1) * max_speed // acceleration_phase
    else:
        deceleration_steps = k - acceleration_phase
        speed = (deceleration_phase - deceleration_steps) * \
            max_speed // deceleration_phase

    return speed


for k in range(0, length):
    x = accelerate_decelerate(k, length)
    y = accelerate_decelerate(k, length)

    if diff_x > 0:
        x = min(x, diff_x)
    else:
        x = max(-x, diff_x)

    if diff_y > 0:
        y = min(y, diff_y)
    else:
        y = max(-y, diff_y)

    diff_x -= x
    diff_y -= y

    print(x, y)
