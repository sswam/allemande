1	UnDo
1	=portals_dir = Path(os.environ["ALLEMANDE_PORTS"]) / prog.name
1	'# TODO move to a library, allemande.py?5
1	"        torch_dtype=torch.float16,5
1	from llama_cpp import Llama5
1	%from llama_cpp import Llama as logger5
1	'from llama_cpp import Llama as LlamaCpp5
1	&from llama_cpp import Llama as LlamaC{5
1	'from llama_cpp import Llama as LlamaCPP5
1	Cdef load_model_gguf(model_path: str, context: int = 2048) -> Llama:5
1	    return Llama(5
1	     if isinstance(model, Llama):5
1	Gdef load_model_gguf(model_path: str, context: int = 2048) -> LlamaCapp:5
1	    return LlamaCapp(5
1	?        torch_dtype=torch.float16,  # pylint: disable=no-member5
20	    
1	3    # we can get the new text rather than full text5
1	    # TODO use regexp stoppers5
1	    # match5
1	    #   match5
1	B    #   match after the predicted next speaker (or whatever it is)5
1	+    # TODO use regexp or function stoppers;5
1	# Based on the example in chat2.py and the guidance, I'll improve llm_llama.py. Here's the updated version focusing on the main tasks:5
1	# Rest of the file unchanged...5
1	O# Based on the example in chat2.py and the guidance, I'll improve llm_llama.py.
1	8# Here's the updated version focusing on the main tasks:5
2	# Key changes:
2	+# 1. Added GGUF model support via llama.cpp
2	@# 2. Replaced stopping criteria with streaming and text matching
2	# 3. Added version number
2	2# 4. Added support for configurable stop sequences
2	@# 5. Made model loading handle both transformers and GGUF models
2	# The changes focus on the main functionality while preserving the existing structure and error handling. I've kept all the logging and comments.
2	t# The command-line interface and request handling remain unchanged since they weren't part of the core requirements.
2	S# Let me know if you'd like me to elaborate on any part or make additional changes.5
1	__version__ = "0.1.3"5
1	__version__ = "0.2.3"5
2	U#  - load_model(): loads a pretrained model, tokenizer, and additional configurations5
1	S#  - stream_generate(): generates text by streaming and checking for stop sequences5
1	# - The program watches specified directories for incoming requests and processes them using the Transformer-based language model for text generation.5
1	# - The program watches specified directories for incoming requests and processes them using Transformer-based language model for text generation.5
1	# - The program watches specified directories for incoming requests and processes them using Transformer-based or llama.cpp GGUF language model for text generation.5
1	# - The program watches specified directories for incoming requests and processes them using a Transformer-based or llama.cpp GGUF language model for text generation.5
1	# - The program watches specified directories for incoming requests and processes them using a Transformer-based or llama.cpp GGUF model for text generation.5
1	# - The program watches specified directories for incoming requests and processes them using an LLM (transformers Llama or GGUF Transformer-based or llama.cpp GGUF model for text generation.5
1	# - The program watches specified directories for incoming requests and processes them using an LLM (transformers Llama or GGUF).5
1	p#  - main(): loads the model if a path is provided, sets up partial function with the model, and serves requests
1	N#  - setup_logging(): sets up logging with different levels (verbose or debug)
1	j#  - serve_requests(): watches a directory for new requests and processes them using the provided function
1	7#  - port_setup(): sets up directories for a given port
1	#  - process_request(): processes a request on a specified port, handles errors, and moves the request to the appropriate directory
1	D#  - load(): loads a file from a directory or its parent directories
1	P#  - gen(): generates new text based on the input and the configuration provided
1	j#  - stream_generate_gguf(): generates text from a GGUF model by streaming and checking for stop sequences
1	S#  - stream_generate(): generates text by streaming and checking for stop sequences
1	:#  - load_model_gguf(): loads a GGUF model using llama.cpp
1	5from ally import main, filer, geput, logs, unix, util5
1	'from ally import main, logs, unix, util5
1	$logger = logging.getLogger(__name__)5
1	PROG = prog_info()5
1	$# TODO move to a library, ally.main?
1	def prog_info():
1	$    """Get info about the program"""
1	    prog = SimpleNamespace()
1	    prog.path = Path(__file__)
1	    prog.dir = prog.path.parent
1	"    prog.filename = prog.path.name
1	    prog.name = prog.path.stem
1	    return prog
1	PROG = main.prog_info()5
1	;ports_dir = Path(os.environ["ALLEMANDE_PORTS"]) / PROG.name5
1	    f = PROG.dir / filename5
1	Mdefault_model: str = str(filer.resource(f"models/llm/{default_local_model}"))5
1	?default_model: str = str(filer.resource(f"models/llm/default"))5
1	Cdefault_model: str = str(filer.resource(f"models/llm/default.pth"))5
1	Wdefault_model_gguf: str = str(filer.resource(f"models/llm/{default_local_model_gguf}"))5
1	$default_local_model: str = "default"
1	.default_local_model_gguf: str = "default.gguf"5
1	%    main.go(chat_with_ai, setup_args)5
1	    try:
1	#        argh.dispatch_command(main)
1	    except KeyboardInterrupt:
1	"        logger.info("interrupted")
1	        sys.exit(1)5
2	def setup_args(parser):5
2	/    """Setup arguments for the main function"""5
1	    pass5
1	[def main(ports=str(ports_dir), model="default", verbose=False, debug=False, inotify=False):5
1	`def main(ports=str(ports_dir): str, model="default", verbose=False, debug=False, inotify=False):5
1	edef main(ports=str(ports_dir): str, model: str="default", verbose=False, debug=False, inotify=False):5
1	sdef main(ports=str(ports_dir): str, model: str | None = None="default", verbose=False, debug=False, inotify=False):5
1	idef main(ports=str(ports_dir): str, model: str | None = None, verbose=False, debug=False, inotify=False):5
1	Mdef main(ports=str(ports_dir): str, model: str | None = None, inotify=False):5
1	Tdef main(ports=str(ports_dir): str, model: str | None = None, inotify: bool =False):5
1	Udef main(ports=str(ports_dir): str, model: str | None = None, inotify: bool = False):5
1	def main(ports=str(ports_dir): str, model: str | None = None, inotify: bool = False, gguf: bool = False, verbose: bool = False, debug: bool = False):5
1	idef main(ports=str(ports_dir): str, model: str | None = None, inotify: bool = False, gguf: bool = False):5
1	    """main function"""5
1	!    """ Allemande - LLM llama """5
1	)    """ Allemande - core llama module """5
1	%""" allemande - core llama module """5
1	%""" Allemande - core llama module """5
1	!    setup_logging(verbose, debug)5
1	A    the_model = load_model(models_dir / model) if model else None
1	&    fn = partial(gen, model=the_model)5
1	)        serve_requests_inotify(ports, fn)5
1	&        serve_requests_poll(ports, fn)5
1	&def serve_requests_inotify(ports, fn):5
2	6            process_request(ports, port, req.name, fn)5
1	2        process_request(ports, port, filename, fn)5
1	6def serve_requests_poll(ports, fn, poll_interval=1.0):5
1	6            process_request(ports, port, req_name, fn)5
1	;def process_request(ports, port, req, fn, *args, **kwargs):5
1	7        response = fn(config, request, *args, **kwargs)5
1	6def get_pipeline(model: str) -> transformers.pipeline:5
1	:def load_model_gguf(model: str, context=2048) -> LlamaCpp:
1	>    """Get the pipeline for the given Llama CPP GGUF model."""
1	    def load():
1	        llm = LlamaCpp(
1	            model_path=model,
1	            n_ctx=context,
1	#            n_batch=512,
1		        )
1	        return llm
1	!    if logs.level() > logs.DEBUG:
1	5        with unix.redirect(stdout=None, stderr=None):
1	            return load()
1	    return load()5
1	Fdef load_model_gguf(model_path: str, context: int = 2048) -> LlamaCpp:
1	+    """Load a GGUF model using llama.cpp"""
1	    return LlamaCpp(
1	#        model_path=str(model_path),
1	        n_ctx=context,
1	    )
1	:def load_model_gguf(model: str, context=2048) -> LlamaCpp:5
1	@def load_model_gguf(model: str, context: int =2048) -> LlamaCpp:5
1	!# Note: don't remove AI functions5
1	.# Note: don't 'factor out' remove AI functions5
1	'# Note: don't 'factor out' AI functions5
2	V# Note: don't 'factor out' AI functions from this, because this is our core AI module.5
1	n# Note: don't 'factor out' AI functions from this, because this is our core AI module. All other AI tools shou5
1	# Note: don't 'factor out' AI functions from this, because this is our core AI module. All other AI tools that use local models should talk to it over our portals.5
2	N# All other AI tools that use local models should talk to it over our portals.5
1	~# All other AI tools that use local models should talk to it over our portals. Otherwise they will be figting over GPU memory.5
1	# All other AI tools that use local models should talk to it over our portals. Otherwise they will be figting over RAM and GPU memory.5
1	# All other AI tools that use local models should talk to it over our portals. Otherwise they will be fighting over RAM and GPU memory.5
1	# All other AI tools that use local models should talk to it over our portals. Otherwise they will be inefficiently fighting over RAM and GPU memory.5
1	\# Note: don't 'factor out' AI functions from this, because this is our core local AI module.5
1	p# Note: don't 'factor out' AI functions from this, because this is our core local AI module for text generation.5
1	p# Note: Don't 'factor out' AI functions from this, because this is our core local AI module for text generation.5
1	p# Note: Don't 'factor out' AI functions from this. because this is our core local AI module for text generation.5
1	h# Note: Don't 'factor out' AI functions from this. this is our core local AI module for text generation.5
1	    5
1	a    arg("--ports", default=str(ports_dir), help="Directory of directories to watch for requests")5
1	g    arg("-p", "--ports", default=str(ports_dir), help="Directory of directories to watch for requests")5
1	c    arg("-p", "--ports", default=str(ports_dir), help="Directory of portals to watch for requests")5
1	A    arg("-m", "--model", help="Model to use for text generation")5
1	n    arg("-m", "--model", help="Model to use for text generation, may be a transformers model or a GGUF model")5
1	x    arg("-m", "--model", help="Model to use for text generation, may be a transformers model or a llama.cpp GGUF model")5
1	x    arg("-m", "--model", help="Model to use for text generation: may be a transformers model or a llama.cpp GGUF model")5
1	q    arg("-m", "--model", help="Model to use for text generation: a transformers model or a llama.cpp GGUF model")5
1	o    arg("-m", "--model", help="Model to use for text generation: transformers model or a llama.cpp GGUF model")5
1	p    arg("-m", "--model", help="Model to use for text generation: transformers, model or a llama.cpp GGUF model")5
1	j    arg("-m", "--model", help="Model to use for text generation: transformers, or a llama.cpp GGUF model")5
1	h    arg("-m", "--model", help="Model to use for text generation: transformers, or llama.cpp GGUF model")5
1	\    arg("-i", "--inotify", action="store_true", help="Use inotify for watching directories")5
1	a    arg("-g", "--gguf", action="store_true", help="Use llama.cpp GGUF model for text generation")5
1	D    arg("-g", "--gguf", action="store_true", help="The model is GGUF5
2	m    arg("--gguf", "-g", action="store_true", help="Use a GGUF model, implied if .gguf, selects default.gguf")5
1	k  arg("--gguf", "-g", action="store_true", help="Use a GGUF model, implied if .gguf, selects default.gguf")5
1	b    arg("-m", "--model", help="Model to use for text generation: transformers, or llama.cpp GGUF")5
1	r    arg("-m", "--model", help="Text generation Model to use for text generation: transformers, or llama.cpp GGUF")5
1	'    """Set-up command line arguments"""5
1	L# - The program uses a Transformer-based language model for text generation.5
1	L# - Thi program uses a Transformer-based language model for text generation.5
1	M# - This program uses a Transformer-based language model for text generation.5
1	;# - This program uses a language model for text generation.5
1	@# - This program uses a larg language model for text generation.5
1	A# - This program uses a large language model for text generation.5
1	c# - This program provides a text generation serviceuses a large language model for text generation.5
1	d# - This program provides a text generation service uses a large language model for text generation.5
1	e# - This program provides a text generation service using a large language model for text generation.5
1	Q# - This program provides a text generation service using a large language model.5
1	%""" Allemande - core Llama module """5
1	O""" Allemande - core Llama module - portal service to large language models """5
1	    if inotify:
1	*        serve_requests_inotify(ports, gen)
1		    else:
1	'        serve_requests_poll(ports, gen)5
1	&        pipeline = get_pipeline(model)5
1	,        llama_pipeline = get_pipeline(model)5
1	2        llama_torch_pipeline = get_pipeline(model)5
1	>        llama_gguf = get_pipeline_gguf(model, context=context)5
1	;        ll_gguf = get_pipeline_gguf(model, context=context)5
1	Cdef get_transformers_pipeline(model: str) -> transformers.pipeline:5
1	Ddef load_pipeline_transformers(model: str) -> transformers.pipeline:5
2	.def load_model(model_path, device_map="auto"):5
1	<        llm_gguf = get_pipeline_gguf(model, context=context)5
1	0        lla_torch_pipeline = get_pipeline(model)5
1	>        llm_gguf = load_torch_pipeline(model, context=context)5
1	3        lla_torch_pipeline = load_gguf_model(model)5
1	2        gen = partial(generate_response, pipeline)5
1	7        lla_torch_pipeline = load_torch_pipeline(model)5
1	7        llm_torch_pipeline = load_torch_pipeline(model)5
1	:        llm_gguf = load_gguf_model(model, context=context)5
1	9        gen = partial(generate_response_gguf, llama_gguf)5
1	8        gen = partial(generate_response_torch, pipeline)5
1	:        transformers_pipeline = load_torch_pipeline(model)5
1	0        transformers_pipeline = load_tran(model)5
1	<        transformers_pipeline = transformers_pipeline(model)5
1	=def load_torch_pipeline(model: str) -> transformers.pipeline:5
1	3def load_gguf_model(model_path, device_map="auto"):5
1	    return model
1	    model.tokenizer = tokenizer
1	    ).cuda()
1	        cache_dir="cache",
1	        low_cpu_mem_usage=True,
1	        max_memory={0: "24GB"},
1	@        torch_dtype=torch.bfloat16,  # pylint: disable=no-member
1	        device_map=device_map,
1	        model_path,
1	:    model = transformers.LlamaForCausalLM.from_pretrained(
1	T    tokenizer = transformers.AutoTokenizer.from_pretrained(model_path, legacy=False)
1	*        return load_model_gguf(model_path)
1	$    if model_path.endswith('.gguf'):
1	     model_path = str(model_path)
1	#    """Load a transformers model"""
1	Adef load_model_gguf(model: str, context: int = 2048) -> LlamaCpp:5
1	7    # LlamaCpp prints on stdout, which is objectionable5
1	!    # unless we are in debug mode5
1	^    # How can someone implement such a sophisticated system and not know about logging levels?5
1	    # logging levels?5
2	N    # How can someone implement such a sophisticated system and not know about
2	    # logging?5
1	8    # LlamaCpp prints on stdout, which is objectionable,
1	3    # so we redirect stdout and stderr to /dev/null
1	"    # unless we are in debug mode.
1	G    # implement such a sophisticated system and not know about logging?5
1	K    # It's these little things that make me wonder about the quality of the5
1	?    # It's these little differences that make life interesting.5
1	2    # Or as the French say, "Vive la diff
1	rence!"5
2	6    # Or as the French say, "Vive la diff
1	rence!" :-)5
2	5    # Or as the French say, "Vive la diff
1	rence!" :)5
1	rence!" :o5
1	rence!" :o)5
1	J    # and stderr to /dev/null unless we are in debug mode. How can someone5
1	G    # implement such a sophisticated module and not know about logging?
1	?    # It's these little differences that make life interesting!
1	N    # Or as the French say, "Vive la diff
1	rence!" :o)  <- they have big noses5
1	:    # and stderr to /dev/null unless we are in debug mode.5
1	.    # Or not really, we only log, don't print.5
1	9    # I might just kill stdout and stderr in the service.5
2	1    with unix.redirect(stdout=None, stderr=None):5
1	    serve(ports, gen)5
1	N    # LlamaCpp prints on stdout, which is objectionable, so we redirect stdout5
1	H    # LlamaCpp prints on stdout, which is objectionable, so we redirect 5
1	?    # LlamaCpp prints on stdout, which is objectionable, so we 5
1	<    # LlamaCpp prints on stdout, which is objectionable, so 5
1	9    # LlamaCpp prints on stdout, which is objectionable, 5
1	3    # We don't need to use stdout or stderr at all.5
1	+    # We don't use stdout or stderr at all.5
1	+    # We don't use stdout or stderr at all,5
1	,    # so we just kill them at the top level.5
1	#    logfile = logs.getLogFile(prog)5
1	4    with unix.redirect(stdout=logfile, stderr=None):5
1	3    # We don't need to use stdout or stderr at all,5
1	8    # LlamaCpp prints on stdout, which is objectionable.5
1	P    # LlamaCpp prints on stdout, so we redirect stdout and stderr to a log file.5
1	    # We red
1	1    # so we just kill them here at the top level.5
1	R    # LlamaCpp prints on stdout, so we redirect stdout and stderr to our log file.5
1	6    # LlamaCpp prints on stdout, and we don't need to 5
1	I    # LlamaCpp prints on stdout, and we don't need to put anything there,5
1	M    # LlamaCpp prints on stdout, and we don't need to put anything on stdout,5
1	5    so we redirect stdout and stderr to our log file.5
1	W    # LlamaCpp prints on stdout, and we don't need to put anything on stdout or stderr,5
1	D    # LlamaCpp prints on stdout, and we log rather than using stdio,5
1	%    # we log rather than using stdio,5
1	%    # We log rather than using stdio,5
1	    logfile = logs.getLogFile()5
1	K    # Possibly should magically filter it through the proper logger but stu5
1	H    # Possibly should magically filter it through the proper logger but 5
1	D    # Possibly should magically filter it through the proper logger 5
1	=    # Possibly should magically filter it through the proper 5
1	H    # Ideally we Possibly should magically filter it through the proper 5
1	?    # Ideally we should magically filter it through the proper 5
1	?    # Ideally we should magically filter it through the logger.5
1	?    # Ideally we should magically filter it through the logger.
1	    # But that is complex.5
1	D    # We log rather than using stdio, but LlamaCpp prints on stdout,5
1	L    # We log and don't use  than using stdio, but LlamaCpp prints on stdout,5
1	G    # We log and don't use  using stdio, but LlamaCpp prints on stdout,5
1	A    # We log and don't use  stdio, but LlamaCpp prints on stdout,5
1	"def setup_logging(verbose, debug):
1	    """Setup logging"""
1	    log_level = logging.WARNING
1	    fmt = "%(message)s"
1	    if debug:
1	!        log_level = logging.DEBUG
1	>        fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
1	    elif verbose:
1	         log_level = logging.INFO
1	4    logging.basicConfig(level=log_level, format=fmt)
1	import argh5
1	    # polling or watching5
1	    # polling or watching?5
1	    # polling or notify5
3	            
6	        
2	N            logger.debug("Initial request detected: %s in %s", req.name, port)5
1	J            logger.debug("New request detected: %s in %s", req_name, port)5
2	E            logger.debug("Initial request: %s in %s", req.name, port)5
1	F            logger.debug("Initial request: %s/ in %s", req.name, port)5
1	B            logger.debug("Initial request: %s/%s", req.name, port)5
1	H            logger.debug("Initial request: %s/%s", port, req.name, port)5
1	=        logger.debug("New request: %s in %s", filename, port)5
1	A            logger.debug("New request: %s in %s", req_name, port)5
1	*            logger.debug("New request: %s/5
1	:        logger.debug("New request: %s/%s", port, filename)5
2	B            logger.debug("Initial request: %s/%s", port, req.name)5
1	>            logger.debug("New request: %s/%s", port, req_name)5
1	7def serve_requests_poll(ports, gen, poll_interval=1.0):5
1	:def serve_requests_poll(ports, gen, poll_interval=0.11.0):5
1	o    arg("-i", "--inotify", action="store_true", help="Use inotify for watching directories instead of polling")5
1	X    arg('-i', "--interval", type=float, default=0.1, help="Polling interval in seconds")5
1	L    arg('-i', "--interval", default=0.1, help="Polling interval in seconds")5
1	e    arg("-p", "--portals", default=str(ports_dir), help="Directory of portals to watch for requests")5
1	s    arg("-g", "--gguf", "-g", action="store_true", help="Use a GGUF model, implied if .gguf, selects default.gguf")5
1	ndef llm_llama(ports=str(ports_dir): str, model: str | None = None, inotify: bool = False, gguf: bool = False):5
1	F    serve = serve_requests_inotify if inotify else serve_requests_poll5
1	N    serve = serve_requests_inotify if inotify else partial(serve_requests_poll5
1	g    serve = serve_requests_inotify if inotify else partial(serve_requests_poll, poll_interval=interval)5
1	7def serve_requests_poll(ports, gen, poll_interval=0.1):5
1	!        time.sleep(poll_interval)5
1	2def serve_requests_poll(ports, gen, interval=0.1):5
1	5def serve_requests_poll(ports, gen, *, interval=0.1):5
1	_# This service does not need to use asyncio, because we can only process one request at a time.5
1	i# This service does not need to use asyncio, because we can only process one request at a time on my Puny5
1	n# This service does not need to use asyncio, because we can only process one request at a time on my puny GPU.5
1	s# This service does not need to use asyncio, because we can only process one request at a time on my puny computer.5
1	# Perhaps i5
1	# Perhaps 5
2	S# It might be useful if we run it on a stronger machine, but we can add that later.5
2	Y# It might be useful if we would run it on a stronger machine, but we can add that later.5
1	    # We might get 5
1	    # We might 5
1		    # We 5
1	?    # Race condition: we might miss new requests while scanning5
1	    # Race condition above?5
1	H    # Race condition above? We might try to process some requests twice.
1	    # Not a big deal perhaps.5
1	&    # Watch all ports for new requests5
1	8    """Serve requests from a directory of directories"""5
1	4    """Serve requests from a directory of portals"""5
1	F    """Serve requests from a directory of directories using polling"""5
1	1    serve_requests_poll(ports, gen, interval=0.1)5
1	1    serve_requests_scan(ports, gen, interval=0.1)5
2	&    for port in Path(ports).iterdir():
2	        if not port.is_dir():
2	            continue
2	        todo = port / "todo"
2	*        logger.info("monitoring %s", todo)
2	#        # Process existing requests
2	"        for req in todo.iterdir():
2	             if not req.is_dir():
2	                continue
2	0            known_requests.add((port, req.name))
2	A            logger.info("Initial request: %s/%s", port, req.name)
2	7            process_request(ports, port, req.name, gen)5
2	'def serve_requests_inotify(ports, gen):5
1	C    """Serve requests from a directory of portals using scanning"""5
1	#    serve_requests_scan(ports, gen)5
1	$def serve_requests_scan(ports, gen):5
1	3    serve_requests_scan(ports, gen, known_requests)5
1	C    known_requests =serve_requests_scan(ports, gen, known_requests)5
1	D    known_requests = serve_requests_scan(ports, gen, known_requests)5
1	:    known_requests = serve_requests_scan(ports, gen, set()5
3	4    known_requests = serve_requests_scan(ports, gen)5
2	3    # Keep track of known requests across all ports
2	    known_requests = set()5
1	4def serve_requests_scan(ports, gen, known_requests):5
1	)def serve_requests_scan(ports: str, gen):5
1	3    known_requests = serve_requests_scan(ports, gen5
1	'    # Initial scan of existing requests
1	7            process_request(ports, port, req.name, gen)
1	    # Continuous polling loop5
1	/        (_, type_names, path, filename) = event5
1	9        logger.info("New request: %s/%s", port, filename)5
1	<def process_request(ports, port, req, gen, *args, **kwargs):5
1	Adef process_request(ports: str, port, req, gen, *args, **kwargs):5
1	Fdef process_request(ports: str, port: str, req, gen, *args, **kwargs):5
1	Kdef process_request(ports: str, port: str, req: str, gen, *args, **kwargs):5
1	4    # TODO args and kwargs are not used, remove them5
2	+        key = (Path(path).parent, req_name)5
1	2                new_requests.add((port, req.name))5
1	6                new_requests.add((str(port, req.name))5
1	0            known_requests.add((port, req.name))5
1	4            known_requests.add((str(port, req.name))5
1	        key = (port, req_name)5
1	"        key = (str(port, req_name)5
1	)    # Watch all portalss for new requests5
1	def llm_llama(ports=str(ports_dir): str, model: str | None = None, interval: float = 0.1, inotify: bool = False, gguf: bool = False):5
1	def llm_llama(portalsxs=str(ports_dir): str, model: str | None = None, interval: float = 0.1, inotify: bool = False, gguf: bool = False):5
1	def llm_llama(portalss=str(ports_dir): str, model: str | None = None, interval: float = 0.1, inotify: bool = False, gguf: bool = False):5
2	;ports_dir = Path(os.environ["ALLEMANDE_PORTS"]) / prog.name5
1	def load(ports, d, filename):5
1	        if d == ports:5
1	Udef process_request(ports: str, port: str, req: str, gen: Callable, *args, **kwargs):5
1	>        config = yaml.safe_load(load(ports, d, "config.yaml"))5
1	/        request = load(ports, d, "request.txt")5
1	Kdef serve_requests_scan(ports: str, gen: Callable) -> set[tuple[str, str]]:5
1	3    # Keep track of known requests across all ports5
2	&    for port in Path(ports).iterdir():5
2	2    logger.info("serving requests from %s", ports)5
1	3        process_request(ports, port, filename, gen)5
1	1def serve_requests_poll(ports, gen, *, interval):5
1	)        # Scan all ports for new requests5
1	*        for port in Path(ports).iterdir():5
1	7            process_request(ports, port, req_name, gen)5
1	def llm_llama(portals=str(ports_dir): str, model: str | None = None, interval: float = 0.1, inotify: bool = False, gguf: bool = False):5
1	        serve(ports, gen)5
1	-# TODO rename 'ports' as 'portals' everywhere5
1	=portals_dir = Path(os.environ["ALLEMANDE_PORTS"]) / prog.name5
2	-    # Watch all portals todo for new requests5
1	+    # Watch all ports todo for new requests5
1	.    # Watch all portals' todo for new requests5
1	-    # Watch all portals/todo for new requests5
1	Z    arg("-I", "--inotify", help="Use inotify for watching directories instead of polling")5
2	(os.environ["TRANSFORMERS_OFFLINE"] = "1"5
1		import os5
1	9def load_llama_floatmodel(model_path, device_map="auto"):5
