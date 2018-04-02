"""
Helper script for finding and doing stuff with broken datasets
"""
from __future__ import print_function


def main():
    args = docopt.docopt(__doc__)
    t0 = time.time()
    try:
        if args['get']:
            return do_get(args)
        elif args['info']:
            return do_info(args)
        elif args['anonymize']:
            return do_anonymize(args)
        elif args['post']:
            return do_post(args)
        elif args['addvar']:
            return do_addvar(args)
        elif args['folderize']:
            return do_folderize(args)
        elif args['loadsave']:
            return do_loadsave(args)
        else:
            raise NotImplementedError(
                "Sorry, that command is not yet implemented.")
    finally:
        print("Elapsed time:", time.time() - t0, "seconds", file=sys.stderr)


if __name__ == '__main__':
    sys.exit(main())

