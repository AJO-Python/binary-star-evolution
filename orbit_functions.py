
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 26 17:31:44 2018

@author: c1672922
"""
import numpy as np
import random

G = 6.674e-11
au = 1.49597e11
pc = 3.0857e16

# =============================================================================
# Functions
# =============================================================================

# =============================================================================
# DATA HANDLING
# =============================================================================


def get_data_ready(filename, num_to_strip=0):
    with open(filename) as f:
        ncols = len(f.readline().split(","))
    masses, rx, ry, rz, vx, vy, vz = np.genfromtxt(filename, delimiter=",")
    masses, rx, ry, rz, vx, vy, vz = clean_data(num_to_strip, masses,
                                                rx, ry, rz, vx, vy, vz)
    return masses, rx, ry, rz, vx, vy, vz


def clean_data(strip_amount, masses, rx, ry, rz, vx, vy, vz):
    x = strip_amount
    masses = masses[x:]
    rx, ry, rz = rx[x:], ry[x:], rz[x:]
    vx, vy, vz = vx[x:], vy[x:], vz[x:]
    return masses, rx, ry, rz, vx, vy, vz


def get_single_data(filename):
    data = np.genfromtxt(filename, delimiter=",", unpack=True)
    return data


def save_interval(masses, pos_x, pos_y, pos_z, vx, vy, vz, dest, index=""):
    vel_x, vel_y, vel_z = vx, vy, vz
    file_data = [masses, pos_x, pos_y, pos_z, vel_x, vel_y, vel_z]
    file_str = ["masses", "pos_x", "pos_y", "pos_z", "vel_x", "vel_y", "vel_z"]
    for index, file_name in enumerate(file_data):
        file_dir = dest + "/" + file_str[index] + ".csv"
        with open(file_dir, "wb") as f:
            np.savetxt(f, file_name, delimiter=",")


def get_init_conds(filename):
    data = []
    with open(filename, "r") as f:
        for line in f:
            line = line.split("=")
            info = line[1]
            info = info.strip()
            data.append(info)
    return data


def clean_results_files(direc):
    file_names = ["/cluster.csv", "/masses.csv",
                  "/sim_time.csv", "/run_time.csv",
                  "/pos_x.csv", "/pos_y.csv", "/pos_z.csv",
                  "/vel_x.csv", "/vel_y.csv", "/vel_z.csv"]
    # Ensuring the files all exist and are empty
    for i in file_names:
        with open(direc + i, "w"):
            pass


def report_snapshot(time, Tmax, masses, vx, vy, vz, rx, ry, rz,
                    N, pos_x, pos_y, pos_z,
                    vel_x, vel_y, vel_z, eps):
    # Setting arrays
    momentum_body, kinetic_body, potential_body = [
            [] for _ in range(3)]
    # Getting the momentum and kinetic energy of each particle
    for i in range(N):
        speed = get_mag([vx[i], vy[i], vz[i]])
        momentum_body.append(get_momentum(speed, masses[i]))
        kinetic_body.append(get_kinetic(speed, masses[i]))
        # Storing the position data
        pos_x[i].append(rx[i])
        pos_y[i].append(ry[i])
        pos_z[i].append(rz[i])
        vel_x[i].append(vx[i])
        vel_y[i].append(vy[i])
        vel_z[i].append(vz[i])

        for j in range(N):
            if i == j:
                potential = 0
            else:
                potential = get_grav_potential(
                        masses[i], masses[j], (rx[i], ry[i], rz[i]),
                        (rx[j], ry[j], rz[j]))
            if (potential not in potential_body) or potential == 0:
                potential_body.append(potential)

    Ek, Ep, Mom = (
            sum(kinetic_body), sum(potential_body), sum(momentum_body))
    return pos_x, pos_y, pos_z, vel_x, vel_y, vel_z, Ek, Ep, Mom

# =============================================================================
# INTEGRATOR
# =============================================================================


def get_accel_soft(N, x, y, z, m, r_min, eps):
    mag_r_min = get_mag(r_min)
    ax = np.zeros(N)
    ay = np.zeros(N)
    az = np.zeros(N)
    for i in range(N):
        for j in range(N):
            if i == j:
                pass
            else:
                x_diff = x[i] - x[j]
                y_diff = y[i] - y[j]
                z_diff = z[i] - z[j]

                R = get_mag([x_diff, y_diff, z_diff])
                if R == 0:
                    raise ValueError("COLLISION")
                elif R < mag_r_min:
                    r_min = [x_diff, y_diff, z_diff]

                f = - (G*m[j]) / ((R**2 + eps**2)**(3/2))

                ax[i] += f * x_diff
                ay[i] += f * y_diff
                az[i] += f * z_diff
    return ax, ay, az, r_min

# =============================================================================
# GET INFORMATION
# =============================================================================


def get_momentum(v, m):
    # Gets momentum of an object
    return v*m


def get_mag(vector):
    vector = np.array(vector, dtype="float64")
    # Gets magnitude of 3D vector
    return np.sqrt((vector[0]**2 + vector[1]**2 + vector[2]**2))


def get_kinetic(v, m):
    # Gets kinetic energy of object
    return 0.5 * m * (v**2)


def get_grav_potential(mass1, mass2, r1, r2):
    dist = np.subtract(r1, r2)
    dist = np.array(dist, dtype=object)
    potential = -G*mass1*mass2 / get_mag(dist)
    if np.isnan(potential):
        print(type(mass1))
        raise ValueError("pair_energy in get_all_pot_energy = nan")
    return potential


def get_total_potential(N, masses, positions):
    potential = 0
    for i in range(N):
        for j in range(N):
            if i != j:
                potential += get_grav_potential(
                        masses[i], masses[j], positions[:, i], positions[:, j])
            else:
                potential += 0
    return potential


def get_com(position, mass):
    com_x = np.average(position[0], axis=0, weights=mass)
    com_y = np.average(position[1], axis=0, weights=mass)
    com_z = np.average(position[2], axis=0, weights=mass)
    com = np.array([com_x, com_y, com_z])
    return com


def get_group_vel(masses, velocities):
    total_mass = sum(masses)
    x, y, z = 0, 0, 0
    for index, mass in enumerate(masses):
        x += velocities[0][index] * mass
        y += velocities[1][index] * mass
        z += velocities[2][index] * mass
    return x/total_mass, y/total_mass, z/total_mass


def get_completion(time, time_max, done):
    done_temp = done
    for i in range(10, -1, -1):
        if time > (time_max*i/10):
            if i not in done_temp:
                done_temp.append(i)
                # print("{} % completed".format(i*10))
                return done
    if done == done_temp:
        return done
# =============================================================================
# GENERATION
# =============================================================================


def gen_masses(N):
    mass_sun = 1.989e30
    masses = np.random.normal(0.2*mass_sun, 0.1*mass_sun, N)
    return masses


def gen_xyz(N, spread):
    return np.random.normal(0, spread, (3, N))


def adjust_pos(position, com):
    for i in range(0, len(position)):
        position[i] = np.subtract(position[i], com[i])
    return position


def gen_cluster(N, mass_dist, pos_dist):
    masses = gen_masses(N)
    positions = gen_xyz(N, pos_dist*au)
    positions = adjust_pos(positions, get_com(positions, masses))
    pos_x = positions[0]
    pos_y = positions[1]
    pos_z = positions[2]
    init_vels = gen_xyz(N, 10e2)
    scaled_vels = np.array(scale_vels(masses, init_vels, positions, 2))
    group_vel = get_group_vel(masses, scaled_vels)
    final_vels = np.zeros((3, N))
    for i in range(3):
        for j in range(N):
            temp = np.subtract(scaled_vels[i, j], group_vel[i])
            final_vels[i, j] = temp
    cluster = np.array((masses, pos_x, pos_y, pos_z, final_vels[0],
                        final_vels[1], final_vels[2]))
    return cluster


def scale_vels(masses, init_vels, positions, virial):
    N = len(masses)
    kinetic = get_kinetic(get_mag(init_vels[:]), masses)
    kinetic_total = sum(kinetic)
    potential = -get_total_potential(N, masses, positions)
    x, y, z = init_vels[:]
    scaling_factor = potential/kinetic_total
    const = np.sqrt(scaling_factor / virial)
    x = x*const
    y = y*const
    z = z*const
    return x, y, z


def gen_filament(Number_Clusters, Bodies_per_Cluster, mass_spread,
                 pos_spread, seed, prog_x, prog_y, prog_z):
    standard_progress = [prog_x, prog_y, prog_z]
    np.random.seed(seed)
    N = Bodies_per_Cluster
    prev_com = [0, 0, 0]
    cluster_list = np.empty((7, N))
    for i in range(Number_Clusters):
        progress = 0

        cluster = gen_cluster(N, mass_spread, pos_spread)
        x_pos = cluster[1]
        y_pos = cluster[2]
        z_pos = cluster[3]
        progress = np.add(filament_progression(
                        standard_progress[0], standard_progress[1],
                        standard_progress[2]), prev_com, dtype="float64")
        x_pos = np.add(x_pos, progress[0])
        y_pos = np.add(y_pos, progress[1])
        z_pos = np.add(z_pos, progress[2])

        cluster_list = [np.append(cluster_list[0], cluster[0]),
                        np.append(cluster_list[1], x_pos),
                        np.append(cluster_list[2], y_pos),
                        np.append(cluster_list[3], z_pos),
                        np.append(cluster_list[4], cluster[4]),
                        np.append(cluster_list[5], cluster[5]),
                        np.append(cluster_list[6], cluster[6])]
        prev_com = get_com((x_pos, y_pos, z_pos), cluster[0])
    for index, array in enumerate(cluster_list):
        cluster_list[index] = cluster_list[index][N:]

    return cluster_list


def filament_progression(x, y, z):
    x_spread = random.randrange(int(x-(x/10000)), int(x+(x/10000)), int(x/1000000))
    y_spread = random.randrange(int(-y/2), int(y/2), int(y/1000))
    z_spread = random.randrange(int(-z/2), int(z/2), int(z/1000))
    result = np.array((x_spread, y_spread, z_spread), dtype="float64")
    return result


def generate_full_filament(destination_directory,
                                  init_conds_directory,
                                  init_conds_name):
        clean_results_files(destination_directory)
        init_vars = get_init_conds(init_conds_directory + init_conds_name)
        init_vars = [int(i) for i in init_vars]
        progression = list((init_vars[-3], init_vars[-2], init_vars[-1]))
        init_vars = init_vars[0:-3]
        # Generating initial_data
        cluster_list = gen_filament(*init_vars, *progression)
        return cluster_list

# =============================================================================
# GRAPHING
# =============================================================================


def min_max(array):
    current_min = 9e99
    current_max = -9e99
    for i in array:
        if min(i) < current_min:
            current_min = min(i)
        if max(i) > current_max:
            current_max = max(i)
    return current_min, current_max

def strip_trailing_data(x, y, z):
    max_length = min(len(x), len(y), len(z))
    x, y, z = x[:max_length], y[:max_length], z[:max_length]
    return x, y, z
