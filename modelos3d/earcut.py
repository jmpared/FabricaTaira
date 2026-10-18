"""Port de mapbox/earcut (ISC) a Python. earcut(data, holeIndices, dim=2) -> lista de índices de triángulos."""
import math

class Node:
    __slots__ = ("i", "x", "y", "prev", "next", "z", "prevZ", "nextZ", "steiner")
    def __init__(self, i, x, y):
        self.i, self.x, self.y = i, x, y
        self.prev = self.next = self.prevZ = self.nextZ = None
        self.z = 0; self.steiner = False

def earcut(data, hole_indices=None, dim=2):
    has_holes = bool(hole_indices)
    outer_len = hole_indices[0] * dim if has_holes else len(data)
    outer = linked_list(data, 0, outer_len, dim, True)
    tris = []
    if outer is None or outer.next is outer.prev: return tris
    if has_holes: outer = eliminate_holes(data, hole_indices, outer, dim)
    min_x = min_y = inv = 0
    if len(data) > 80 * dim:
        xs = data[0:outer_len:dim]; ys = data[1:outer_len:dim]
        min_x, min_y = min(xs), min(ys); max_x, max_y = max(xs), max(ys)
        inv = max(max_x - min_x, max_y - min_y); inv = 32767 / inv if inv != 0 else 0
    earcut_linked(outer, tris, dim, min_x, min_y, inv, 0)
    return tris

def linked_list(data, start, end, dim, clockwise):
    last = None
    if clockwise == (signed_area(data, start, end, dim) > 0):
        for i in range(start, end, dim): last = insert_node(i // dim, data[i], data[i + 1], last)
    else:
        for i in range(end - dim, start - 1, -dim): last = insert_node(i // dim, data[i], data[i + 1], last)
    if last and equals(last, last.next):
        remove_node(last); last = last.next
    return last

def filter_points(start, end=None):
    if start is None: return start
    if end is None: end = start
    p = start
    while True:
        again = False
        if not p.steiner and (equals(p, p.next) or area(p.prev, p, p.next) == 0):
            remove_node(p); p = end = p.prev
            if p is p.next: break
            again = True
        else:
            p = p.next
        if not (again or p is not end): break
    return end

def earcut_linked(ear, tris, dim, min_x, min_y, inv, pas):
    if ear is None: return
    if not pas and inv: index_curve(ear, min_x, min_y, inv)
    stop = ear
    while ear.prev is not ear.next:
        prev, nxt = ear.prev, ear.next
        if (is_ear_hashed(ear, min_x, min_y, inv) if inv else is_ear(ear)):
            tris.extend([prev.i, ear.i, nxt.i])
            remove_node(ear)
            ear = nxt.next; stop = nxt.next
            continue
        ear = nxt
        if ear is stop:
            if not pas:
                earcut_linked(filter_points(ear), tris, dim, min_x, min_y, inv, 1)
            elif pas == 1:
                ear = cure_local_intersections(filter_points(ear), tris, dim)
                earcut_linked(ear, tris, dim, min_x, min_y, inv, 2)
            elif pas == 2:
                split_earcut(ear, tris, dim, min_x, min_y, inv)
            break

def is_ear(ear):
    a, b, c = ear.prev, ear, ear.next
    if area(a, b, c) >= 0: return False
    x0, x1 = min(a.x, b.x, c.x), max(a.x, b.x, c.x); y0, y1 = min(a.y, b.y, c.y), max(a.y, b.y, c.y)
    p = c.next
    while p is not a:
        if (x0 <= p.x <= x1 and y0 <= p.y <= y1 and point_in_triangle(a.x, a.y, b.x, b.y, c.x, c.y, p.x, p.y)
                and area(p.prev, p, p.next) >= 0): return False
        p = p.next
    return True

def is_ear_hashed(ear, min_x, min_y, inv):
    a, b, c = ear.prev, ear, ear.next
    if area(a, b, c) >= 0: return False
    x0, x1 = min(a.x, b.x, c.x), max(a.x, b.x, c.x); y0, y1 = min(a.y, b.y, c.y), max(a.y, b.y, c.y)
    min_z = z_order(x0, y0, min_x, min_y, inv); max_z = z_order(x1, y1, min_x, min_y, inv)
    p, n = ear.prevZ, ear.nextZ
    while p and p.z >= min_z and n and n.z <= max_z:
        if (x0 <= p.x <= x1 and y0 <= p.y <= y1 and p is not a and p is not c and
                point_in_triangle(a.x, a.y, b.x, b.y, c.x, c.y, p.x, p.y) and area(p.prev, p, p.next) >= 0): return False
        p = p.prevZ
        if (x0 <= n.x <= x1 and y0 <= n.y <= y1 and n is not a and n is not c and
                point_in_triangle(a.x, a.y, b.x, b.y, c.x, c.y, n.x, n.y) and area(n.prev, n, n.next) >= 0): return False
        n = n.nextZ
    while p and p.z >= min_z:
        if (x0 <= p.x <= x1 and y0 <= p.y <= y1 and p is not a and p is not c and
                point_in_triangle(a.x, a.y, b.x, b.y, c.x, c.y, p.x, p.y) and area(p.prev, p, p.next) >= 0): return False
        p = p.prevZ
    while n and n.z <= max_z:
        if (x0 <= n.x <= x1 and y0 <= n.y <= y1 and n is not a and n is not c and
                point_in_triangle(a.x, a.y, b.x, b.y, c.x, c.y, n.x, n.y) and area(n.prev, n, n.next) >= 0): return False
        n = n.nextZ
    return True

def cure_local_intersections(start, tris, dim):
    p = start
    while True:
        a, b = p.prev, p.next.next
        if not equals(a, b) and intersects(a, p, p.next, b) and locally_inside(a, b) and locally_inside(b, a):
            tris.extend([a.i, p.i, b.i])
            remove_node(p); remove_node(p.next)
            p = start = b
        p = p.next
        if p is start: break
    return filter_points(p)

def split_earcut(start, tris, dim, min_x, min_y, inv):
    a = start
    while True:
        b = a.next.next
        while b is not a.prev:
            if a.i != b.i and is_valid_diagonal(a, b):
                c = split_polygon(a, b)
                a = filter_points(a, a.next); c = filter_points(c, c.next)
                earcut_linked(a, tris, dim, min_x, min_y, inv, 0)
                earcut_linked(c, tris, dim, min_x, min_y, inv, 0)
                return
            b = b.next
        a = a.next
        if a is start: break

def eliminate_holes(data, hole_indices, outer, dim):
    queue = []
    for k, h in enumerate(hole_indices):
        start = h * dim
        end = hole_indices[k + 1] * dim if k < len(hole_indices) - 1 else len(data)
        lst = linked_list(data, start, end, dim, False)
        if lst is lst.next: lst.steiner = True
        queue.append(get_leftmost(lst))
    queue.sort(key=lambda n: (n.x, n.y))
    for h in queue:
        outer = eliminate_hole(h, outer)
    return outer

def eliminate_hole(hole, outer):
    bridge = find_hole_bridge(hole, outer)
    if bridge is None: return outer
    bridge_rev = split_polygon(bridge, hole)
    filter_points(bridge_rev, bridge_rev.next)
    return filter_points(bridge, bridge.next)

def find_hole_bridge(hole, outer):
    p = outer; hx, hy = hole.x, hole.y; qx = -math.inf; m = None
    if equals(hole, p): return p
    while True:
        if equals(hole, p.next): return p.next
        if hy <= p.y and hy >= p.next.y and p.next.y != p.y:
            x = p.x + (hy - p.y) * (p.next.x - p.x) / (p.next.y - p.y)
            if hx >= x > qx:
                qx = x; m = p if p.x < p.next.x else p.next
                if x == hx: return m
        p = p.next
        if p is outer: break
    if m is None: return None
    stop = m; mx, my = m.x, m.y; tan_min = math.inf
    p = m
    while True:
        if (hx >= p.x >= mx and hx != p.x and
                point_in_triangle(hx if hy < my else qx, hy, mx, my, qx if hy < my else hx, hy, p.x, p.y)):
            tan = abs(hy - p.y) / (hx - p.x)
            if locally_inside(p, hole) and (tan < tan_min or (tan == tan_min and (p.x > m.x or (p.x == m.x and sector_contains_sector(m, p))))):
                m = p; tan_min = tan
        p = p.next
        if p is stop: break
    return m

def sector_contains_sector(m, p):
    return area(m.prev, m, p.prev) < 0 and area(p.next, m, m.next) < 0

def index_curve(start, min_x, min_y, inv):
    p = start
    while True:
        if p.z == 0: p.z = z_order(p.x, p.y, min_x, min_y, inv)
        p.prevZ = p.prev; p.nextZ = p.next; p = p.next
        if p is start: break
    p.prevZ.nextZ = None; p.prevZ = None
    sort_linked(p)

def sort_linked(lst):
    in_size = 1
    while True:
        p = lst; lst = None; tail = None; num_merges = 0
        while p:
            num_merges += 1; q = p; p_size = 0
            for _ in range(in_size):
                p_size += 1; q = q.nextZ
                if not q: break
            q_size = in_size
            while p_size > 0 or (q_size > 0 and q):
                if p_size != 0 and (q_size == 0 or not q or p.z <= q.z):
                    e = p; p = p.nextZ; p_size -= 1
                else:
                    e = q; q = q.nextZ; q_size -= 1
                if tail: tail.nextZ = e
                else: lst = e
                e.prevZ = tail; tail = e
            p = q
        tail.nextZ = None; in_size *= 2
        if num_merges <= 1: return lst

def z_order(x, y, min_x, min_y, inv):
    x = int((x - min_x) * inv) & 0xFFFFFFFF; y = int((y - min_y) * inv) & 0xFFFFFFFF
    x = (x | (x << 8)) & 0x00FF00FF; x = (x | (x << 4)) & 0x0F0F0F0F; x = (x | (x << 2)) & 0x33333333; x = (x | (x << 1)) & 0x55555555
    y = (y | (y << 8)) & 0x00FF00FF; y = (y | (y << 4)) & 0x0F0F0F0F; y = (y | (y << 2)) & 0x33333333; y = (y | (y << 1)) & 0x55555555
    return x | (y << 1)

def get_leftmost(start):
    p = start; left = start
    while True:
        if p.x < left.x or (p.x == left.x and p.y < left.y): left = p
        p = p.next
        if p is start: break
    return left

def point_in_triangle(ax, ay, bx, by, cx, cy, px, py):
    return ((cx - px) * (ay - py) >= (ax - px) * (cy - py) and (ax - px) * (by - py) >= (bx - px) * (ay - py)
            and (bx - px) * (cy - py) >= (cx - px) * (by - py))

def is_valid_diagonal(a, b):
    return (a.next.i != b.i and a.prev.i != b.i and not intersects_polygon(a, b) and
            (locally_inside(a, b) and locally_inside(b, a) and middle_inside(a, b) and
             (area(a.prev, a, b.prev) or area(a, b.prev, b)) or
             equals(a, b) and area(a.prev, a, a.next) > 0 and area(b.prev, b, b.next) > 0))

def area(p, q, r): return (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)
def equals(p1, p2): return p1.x == p2.x and p1.y == p2.y

def intersects(p1, q1, p2, q2):
    o1, o2, o3, o4 = sign(area(p1, q1, p2)), sign(area(p1, q1, q2)), sign(area(p2, q2, p1)), sign(area(p2, q2, q1))
    if o1 != o2 and o3 != o4: return True
    if o1 == 0 and on_segment(p1, p2, q1): return True
    if o2 == 0 and on_segment(p1, q2, q1): return True
    if o3 == 0 and on_segment(p2, p1, q2): return True
    if o4 == 0 and on_segment(p2, q1, q2): return True
    return False

def on_segment(p, q, r):
    return min(p.x, r.x) <= q.x <= max(p.x, r.x) and min(p.y, r.y) <= q.y <= max(p.y, r.y)

def sign(v): return (v > 0) - (v < 0)

def intersects_polygon(a, b):
    p = a
    while True:
        if p.i != a.i and p.next.i != a.i and p.i != b.i and p.next.i != b.i and intersects(p, p.next, a, b): return True
        p = p.next
        if p is a: break
    return False

def locally_inside(a, b):
    return (area(a, b, a.next) >= 0 and area(a, a.prev, b) >= 0) if area(a.prev, a, a.next) < 0 else \
           (area(a, b, a.prev) < 0 or area(a, a.next, b) < 0)

def middle_inside(a, b):
    p = a; inside = False; px, py = (a.x + b.x) / 2, (a.y + b.y) / 2
    while True:
        if ((p.y > py) != (p.next.y > py)) and p.next.y != p.y and px < (p.next.x - p.x) * (py - p.y) / (p.next.y - p.y) + p.x:
            inside = not inside
        p = p.next
        if p is a: break
    return inside

def split_polygon(a, b):
    a2 = Node(a.i, a.x, a.y); b2 = Node(b.i, b.x, b.y)
    an, bp = a.next, b.prev
    a.next = b; b.prev = a
    a2.next = an; an.prev = a2
    b2.next = a2; a2.prev = b2
    bp.next = b2; b2.prev = bp
    return b2

def insert_node(i, x, y, last):
    p = Node(i, x, y)
    if last is None:
        p.prev = p; p.next = p
    else:
        p.next = last.next; p.prev = last; last.next.prev = p; last.next = p
    return p

def remove_node(p):
    p.next.prev = p.prev; p.prev.next = p.next
    if p.prevZ: p.prevZ.nextZ = p.nextZ
    if p.nextZ: p.nextZ.prevZ = p.prevZ

def signed_area(data, start, end, dim):
    s = 0; j = end - dim
    for i in range(start, end, dim):
        s += (data[j] - data[i]) * (data[i + 1] + data[j + 1]); j = i
    return s
