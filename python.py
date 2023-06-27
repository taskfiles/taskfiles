from invoke import Context, task


@task()
def clean_pyc(ctx: Context):
    ctx.run("find ./ -name '*.pyc'")
