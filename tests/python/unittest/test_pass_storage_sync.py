import tvm

def test_storage_sync():
    m = tvm.Var('m')
    l = tvm.Var('l')
    A = tvm.placeholder((m, l), name='A')

    A1 = tvm.compute((m, l), lambda i, j: A[i, j], name='A1')
    A2 = tvm.compute((m, l), lambda i, j: A1[i, j] + 3, name='A2')

    s = tvm.Schedule(A2.op)
    block_x = tvm.IterVar(thread_tag="blockIdx.x")
    xo, xi = s[A2].split(A2.op.axis[0], factor=8, outer=block_x)
    s[A1].compute_at(s[A2], xo)
    s[A1].set_scope("shared")

    bounds = tvm.schedule.InferBound(s)
    assert isinstance(bounds, tvm.collections.Map)
    stmt = tvm.schedule.ScheduleOps(s, bounds)

    Ab = tvm.Buffer(A.shape, A.dtype, name='A')
    A2b = tvm.Buffer(A2.shape, A2.dtype, name='A2')
    stmt = tvm.ir_pass.StorageFlatten(stmt, {A: Ab, A2: A2b})
    f = tvm.ir_pass.MakeAPI(stmt, "test", [Ab, A2b], 2)
    flist = tvm.ir_pass.SplitHostDevice(f)
    f = flist[1]
    f = tvm.ir_pass.StorageSync(f, "shared")
    print(f.body)

if __name__ == "__main__":
    test_storage_sync()