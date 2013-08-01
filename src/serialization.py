Constructors = {}

def register( constructor, constructor_name = None ):
    if not constructor_name:
        constructor_name = constructor.name
    Constructors[ constructor_name ] = constructor

def create_original( constructor_name, context, **kwargs ):
    x = dict(context)
    x.update( kwargs )
    rv = Constructors[ constructor_name ]( **x )
    rv.serialization_args = kwargs
    rv.serialization_constructor_name = constructor_name
    return rv

def serialize_original( x ):
    return (x.serialization_constructor_name, x.serialization_args)

def unserialize_original( ctx, serialized ):
    name, args = serialized
    return create_original( name, ctx, **args )
