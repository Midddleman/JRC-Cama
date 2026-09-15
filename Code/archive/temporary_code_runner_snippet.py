   for out_row in range(out_rows):
                    for out_col in range(out_width):
                        if water_count[out_row, out_col] < min_connected_water_cells:
                            continue
                        if water_ratio[out_row, out_col] > water_ratio_threshold:
                            water_connected[out_row, out_col] = True
                            continue